from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from engineering_graph.execution import ExecutionAllocation, ExecutionManifest, ExecutionWave
from engineering_graph.runner import AgentRun, RunnerRegistry
from engineering_graph.supervisor import start_supervisor_job, supervisor_tick


class AgentSupervisorParallelTests(unittest.TestCase):
    def test_two_slots_launch_two_then_repeat_tick_is_idempotent_and_settles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            execution_root = root / ".execution"
            settings = SimpleNamespace(
                repository_id="az1nn/cpxlabs-admin",
                repo_root=root,
                tool_root=root / "engineering-graph",
            )
            tasks = (
                "SPEC-014-AGENT-SUPERVISOR:T040",
                "SPEC-014-AGENT-SUPERVISOR:T041",
            )
            manifest = ExecutionManifest(
                repository=settings.repository_id,
                source_revision="abc123",
                spec_id="SPEC-014-AGENT-SUPERVISOR",
                agent="codex",
                ready=tasks,
                blocked=(),
                cycles=(),
                conflicts=(),
                waves=(ExecutionWave(index=1, tasks=tasks),),
                generated_at="2026-09-14T00:00:00+00:00",
            )
            runs: list[AgentRun] = []

            def allocation(task_id: str) -> ExecutionAllocation:
                return ExecutionAllocation(
                    repository=settings.repository_id,
                    task_id=task_id,
                    spec_id="SPEC-014-AGENT-SUPERVISOR",
                    source_revision="abc123",
                    agent="codex",
                    branch=f"task/{task_id.rsplit(':', 1)[-1].lower()}",
                    worktree_path="/tmp/worktree",
                    context_path="/tmp/context.json",
                    handoff_path="/tmp/codex.md",
                    lease_status="active",
                    validation_commands=(),
                    created_at="2026-09-14T00:00:00+00:00",
                    updated_at="2026-09-14T00:00:00+00:00",
                )

            def registry(*_args, **_kwargs) -> RunnerRegistry:
                return RunnerRegistry(settings.repository_id, tuple(runs))

            def start(_settings, task_id, argv, **_kwargs) -> AgentRun:
                index = len(runs) + 1
                run = AgentRun(
                    run_id=f"run-{index}",
                    repository=settings.repository_id,
                    task_id=task_id,
                    spec_id="SPEC-014-AGENT-SUPERVISOR",
                    source_revision="abc123",
                    agent="codex",
                    branch="task/test",
                    worktree_path="/tmp/worktree",
                    handoff_path="/tmp/codex.md",
                    context_path="/tmp/context.json",
                    argv=tuple(argv),
                    stdin_handoff=False,
                    pid=1000 + index,
                    process_fingerprint=f"linux-proc:{1000 + index}:1",
                    process_group_id=1000 + index,
                    status="running",
                    exit_code=None,
                    stop_requested=False,
                    stdout_path=f"/tmp/run-{index}/stdout.log",
                    stderr_path=f"/tmp/run-{index}/stderr.log",
                    result_path=f"/tmp/run-{index}/result.json",
                    created_at=f"2026-09-14T00:00:0{index}+00:00",
                    started_at=f"2026-09-14T00:00:0{index}+00:00",
                    finished_at=None,
                    updated_at=f"2026-09-14T00:00:0{index}+00:00",
                )
                runs.append(run)
                return run

            with (
                patch("engineering_graph.supervisor.current_revision", return_value="abc123"),
                patch(
                    "engineering_graph.supervisor.load_active_allocation",
                    side_effect=lambda _settings, task_id, **_kwargs: allocation(task_id),
                ),
                patch("engineering_graph.supervisor.reconcile_registry", side_effect=registry),
                patch("engineering_graph.supervisor.start_run", side_effect=start),
            ):
                job = start_supervisor_job(
                    settings,
                    manifest,
                    Path("/tmp/manifest.json"),
                    1,
                    ("python", "fixture.py"),
                    max_parallel=2,
                    max_attempts=1,
                    root_override=execution_root,
                )
                self.assertEqual([run.task_id for run in runs], list(tasks))
                self.assertEqual([task.status for task in job.tasks], ["running", "running"])

                job = supervisor_tick(settings, job.job_id, root_override=execution_root)
                self.assertEqual(len(runs), 2)
                self.assertEqual([task.status for task in job.tasks], ["running", "running"])

                runs[:] = [
                    replace(
                        run,
                        status="succeeded",
                        exit_code=0,
                        finished_at="2026-09-14T00:02:00+00:00",
                        updated_at="2026-09-14T00:02:00+00:00",
                    )
                    for run in runs
                ]
                job = supervisor_tick(settings, job.job_id, root_override=execution_root)
                self.assertEqual(job.status, "settled")
                self.assertEqual([task.status for task in job.tasks], ["succeeded", "succeeded"])
                self.assertEqual(len(runs), 2)


if __name__ == "__main__":
    unittest.main()
