from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from engineering_graph.execution import ExecutionAllocation, ExecutionManifest, ExecutionWave
from engineering_graph.runner import AgentRun, RunnerRegistry
from engineering_graph.supervisor import (
    SupervisorCollisionError,
    SupervisorError,
    create_supervisor_job,
    start_supervisor_job,
    stop_supervisor_job,
    supervisor_tick,
)


class AgentSupervisorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.execution_root = root / ".execution"
        self.settings = SimpleNamespace(
            repository_id="az1nn/cpxlabs-admin",
            repo_root=root,
            tool_root=root / "engineering-graph",
        )
        self.task_a = "SPEC-014-AGENT-SUPERVISOR:T040"
        self.task_b = "SPEC-014-AGENT-SUPERVISOR:T041"
        self.manifest = ExecutionManifest(
            repository=self.settings.repository_id,
            source_revision="abc123",
            spec_id="SPEC-014-AGENT-SUPERVISOR",
            agent="codex",
            ready=(self.task_a, self.task_b),
            blocked=(),
            cycles=(),
            conflicts=(),
            waves=(ExecutionWave(index=1, tasks=(self.task_a, self.task_b)),),
            generated_at="2026-09-14T00:00:00+00:00",
        )
        self.runs: list[AgentRun] = []
        self.counter = 0

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def allocation(self, task_id: str) -> ExecutionAllocation:
        return ExecutionAllocation(
            repository=self.settings.repository_id,
            task_id=task_id,
            spec_id="SPEC-014-AGENT-SUPERVISOR",
            source_revision="abc123",
            agent="codex",
            branch=f"task/{task_id.rsplit(':', 1)[-1].lower()}",
            worktree_path=f"/tmp/{task_id.rsplit(':', 1)[-1].lower()}",
            context_path="/tmp/context.json",
            handoff_path="/tmp/codex.md",
            lease_status="active",
            validation_commands=(),
            created_at="2026-09-14T00:00:00+00:00",
            updated_at="2026-09-14T00:00:00+00:00",
        )

    def runner_registry(self, *_args, **_kwargs) -> RunnerRegistry:
        return RunnerRegistry(self.settings.repository_id, tuple(self.runs))

    def fake_start(self, _settings, task_id, argv, **_kwargs) -> AgentRun:
        self.counter += 1
        run = AgentRun(
            run_id=f"run-{self.counter}",
            repository=self.settings.repository_id,
            task_id=task_id,
            spec_id="SPEC-014-AGENT-SUPERVISOR",
            source_revision="abc123",
            agent="codex",
            branch=f"task/{task_id.rsplit(':', 1)[-1].lower()}",
            worktree_path="/tmp/worktree",
            handoff_path="/tmp/codex.md",
            context_path="/tmp/context.json",
            argv=tuple(argv),
            stdin_handoff=True,
            pid=1000 + self.counter,
            process_fingerprint=f"linux-proc:{1000 + self.counter}:1",
            process_group_id=1000 + self.counter,
            status="running",
            exit_code=None,
            stop_requested=False,
            stdout_path=f"/tmp/run-{self.counter}/stdout.log",
            stderr_path=f"/tmp/run-{self.counter}/stderr.log",
            result_path=f"/tmp/run-{self.counter}/result.json",
            created_at=f"2026-09-14T00:00:0{self.counter}+00:00",
            started_at=f"2026-09-14T00:00:0{self.counter}+00:00",
            finished_at=None,
            updated_at=f"2026-09-14T00:00:0{self.counter}+00:00",
        )
        self.runs.append(run)
        return run

    def patches(self):
        return (
            patch("engineering_graph.supervisor.current_revision", return_value="abc123"),
            patch(
                "engineering_graph.supervisor.load_active_allocation",
                side_effect=lambda _settings, task_id, **_kwargs: self.allocation(task_id),
            ),
            patch(
                "engineering_graph.supervisor.reconcile_registry",
                side_effect=self.runner_registry,
            ),
            patch("engineering_graph.supervisor.start_run", side_effect=self.fake_start),
        )

    def test_tick_respects_parallel_limit_and_wave_order(self) -> None:
        p1, p2, p3, p4 = self.patches()
        with p1, p2, p3, p4:
            job = start_supervisor_job(
                self.settings,
                self.manifest,
                Path("/tmp/manifest.json"),
                1,
                ("python", "fixture.py"),
                max_parallel=1,
                max_attempts=2,
                stdin_handoff=True,
                root_override=self.execution_root,
            )
            self.assertEqual([run.task_id for run in self.runs], [self.task_a])
            self.assertEqual([task.status for task in job.tasks], ["running", "pending"])

            self.runs[0] = replace(
                self.runs[0],
                status="succeeded",
                exit_code=0,
                finished_at="2026-09-14T00:01:00+00:00",
                updated_at="2026-09-14T00:01:00+00:00",
            )
            job = supervisor_tick(
                self.settings,
                job.job_id,
                root_override=self.execution_root,
            )
            self.assertEqual(
                [run.task_id for run in self.runs],
                [self.task_a, self.task_b],
            )
            self.assertEqual([task.status for task in job.tasks], ["succeeded", "running"])

    def test_failed_run_exhausts_then_next_task_uses_slot(self) -> None:
        p1, p2, p3, p4 = self.patches()
        with p1, p2, p3, p4:
            job = start_supervisor_job(
                self.settings,
                self.manifest,
                Path("/tmp/manifest.json"),
                1,
                ("python", "fixture.py"),
                max_parallel=1,
                max_attempts=1,
                root_override=self.execution_root,
            )
            self.runs[0] = replace(
                self.runs[0],
                status="failed",
                exit_code=2,
                finished_at="2026-09-14T00:01:00+00:00",
                updated_at="2026-09-14T00:01:00+00:00",
            )
            job = supervisor_tick(
                self.settings,
                job.job_id,
                root_override=self.execution_root,
            )
            self.assertEqual(job.tasks[0].status, "exhausted")
            self.assertEqual(job.tasks[0].attempts, 1)
            self.assertEqual(job.tasks[1].status, "running")
            self.assertEqual([run.task_id for run in self.runs], [self.task_a, self.task_b])

    def test_failed_run_retries_before_later_wave_peer(self) -> None:
        p1, p2, p3, p4 = self.patches()
        with p1, p2, p3, p4:
            job = start_supervisor_job(
                self.settings,
                self.manifest,
                Path("/tmp/manifest.json"),
                1,
                ("python", "fixture.py"),
                max_parallel=1,
                max_attempts=2,
                root_override=self.execution_root,
            )
            self.runs[0] = replace(
                self.runs[0],
                status="orphaned",
                finished_at="2026-09-14T00:01:00+00:00",
                updated_at="2026-09-14T00:01:00+00:00",
            )
            job = supervisor_tick(
                self.settings,
                job.job_id,
                root_override=self.execution_root,
            )
            self.assertEqual([run.task_id for run in self.runs], [self.task_a, self.task_a])
            self.assertEqual(job.tasks[0].attempts, 2)
            self.assertEqual(job.tasks[0].status, "running")
            self.assertEqual(job.tasks[1].status, "pending")

    def test_stopped_run_is_not_retried(self) -> None:
        p1, p2, p3, p4 = self.patches()
        with p1, p2, p3, p4:
            job = start_supervisor_job(
                self.settings,
                self.manifest,
                Path("/tmp/manifest.json"),
                1,
                ("python", "fixture.py"),
                max_parallel=1,
                max_attempts=2,
                root_override=self.execution_root,
            )
            self.runs[0] = replace(
                self.runs[0],
                status="stopped",
                exit_code=-15,
                stop_requested=True,
                finished_at="2026-09-14T00:01:00+00:00",
                updated_at="2026-09-14T00:01:00+00:00",
            )
            job = supervisor_tick(
                self.settings,
                job.job_id,
                root_override=self.execution_root,
            )
            self.assertEqual(job.tasks[0].status, "stopped")
            self.assertEqual(job.tasks[0].attempts, 1)
            self.assertEqual(self.runs[1].task_id, self.task_b)
            self.assertEqual(sum(run.task_id == self.task_a for run in self.runs), 1)

    def test_active_supervisors_cannot_claim_same_task(self) -> None:
        p1, p2, p3, p4 = self.patches()
        with p1, p2, p3, p4:
            create_supervisor_job(
                self.settings,
                self.manifest,
                Path("/tmp/manifest.json"),
                1,
                ("python", "fixture.py"),
                root_override=self.execution_root,
            )
            with self.assertRaises(SupervisorCollisionError):
                create_supervisor_job(
                    self.settings,
                    self.manifest,
                    Path("/tmp/manifest.json"),
                    1,
                    ("python", "fixture.py"),
                    root_override=self.execution_root,
                )

    def test_stop_fails_closed_when_latest_run_is_not_job_owned(self) -> None:
        p1, p2, p3, p4 = self.patches()
        with p1, p2, p3, p4:
            job = start_supervisor_job(
                self.settings,
                self.manifest,
                Path("/tmp/manifest.json"),
                1,
                ("python", "fixture.py"),
                max_parallel=1,
                root_override=self.execution_root,
            )
            foreign = replace(
                self.runs[0],
                run_id="foreign-run",
                created_at="2026-09-14T00:10:00+00:00",
                updated_at="2026-09-14T00:10:00+00:00",
            )
            self.runs.append(foreign)
            with patch("engineering_graph.supervisor.stop_run") as stop:
                with self.assertRaises(SupervisorError):
                    stop_supervisor_job(
                        self.settings,
                        job.job_id,
                        root_override=self.execution_root,
                    )
                stop.assert_not_called()


if __name__ == "__main__":
    unittest.main()
