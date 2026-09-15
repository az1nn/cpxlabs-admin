from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from engineering_graph.config import ContextBudget, GraphSettings, Neo4jSettings
from engineering_graph.execution import planned_allocation
from engineering_graph.leases import acquire_lease, active_lease, load_registry
from engineering_graph.runner import AgentRun, RunnerRegistry, registry_path, save_runner_registry
from engineering_graph.supervisor import SupervisorJob, SupervisorTask
from engineering_graph.validation import ValidationError, run_validation, status_validations
from engineering_graph.worktrees import branch_name_for_task, current_revision, ensure_worktree, worktree_path_for_task


class AgentValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        subprocess.run(["git", "init"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "validator@example.test"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Validator Test"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/example/validator.git"],
            cwd=self.repo,
            check=True,
        )
        (self.repo / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=self.repo, check=True, capture_output=True)

        self.execution_root = self.repo / ".execution-test"
        self.task_id = "SPEC-015-AGENT-VALIDATOR:T040"
        self.settings = GraphSettings(
            tool_root=self.repo / "engineering-graph",
            repo_root=self.repo,
            repository_id="example/validator",
            neo4j=Neo4jSettings("bolt://unused", "neo4j", "unused", "neo4j"),
            context=ContextBudget(3, 80),
            validation_rules={},
            historical_spec_prefixes=(),
            specs_glob="specs/[0-9][0-9][0-9]-*/spec.md",
            tasks_name="tasks.md",
            plans_name="plan.md",
            adr_glob="docs/adr/[0-9][0-9][0-9][0-9]-*.md",
            prune_stale=True,
        )
        self.revision = current_revision(self.repo)
        self.branch = branch_name_for_task(self.task_id)
        self.worktree = worktree_path_for_task(self.execution_root, self.task_id)
        ensure_worktree(self.repo, path=self.worktree, branch=self.branch, source_revision=self.revision)
        context_dir = self.execution_root / "contexts" / "spec-015-agent-validator-t040"
        context_dir.mkdir(parents=True, exist_ok=True)
        self.context = context_dir / "context.json"
        self.handoff = context_dir / "codex.md"
        self.context.write_text('{"fixture": true}\n', encoding="utf-8")
        self.handoff.write_text("VALIDATOR_HANDOFF_FIXTURE\n", encoding="utf-8")
        self._install_allocation((f"{sys.executable} -c \"print('first-ok')\"", f"{sys.executable} -c \"print('second-ok')\""))
        self._install_run("succeeded")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _install_allocation(self, commands: tuple[str, ...]) -> None:
        allocation = planned_allocation(
            repository=self.settings.repository_id,
            task_id=self.task_id,
            spec_id="SPEC-015-AGENT-VALIDATOR",
            source_revision=self.revision,
            agent="codex",
            branch=self.branch,
            worktree_path=str(self.worktree),
            context_path=str(self.context),
            handoff_path=str(self.handoff),
            validation_commands=commands,
        )
        lease_path = self.execution_root / "leases.json"
        if lease_path.exists():
            lease_path.unlink()
        acquire_lease(lease_path, allocation)

    def _run(self, status: str, run_id: str = "run-success") -> AgentRun:
        run_dir = self.execution_root / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        now = "2026-09-15T00:00:00+00:00"
        return AgentRun(
            run_id=run_id,
            repository=self.settings.repository_id,
            task_id=self.task_id,
            spec_id="SPEC-015-AGENT-VALIDATOR",
            source_revision=self.revision,
            agent="codex",
            branch=self.branch,
            worktree_path=str(self.worktree),
            handoff_path=str(self.handoff),
            context_path=str(self.context),
            argv=(sys.executable, "-c", "pass"),
            stdin_handoff=False,
            pid=None,
            process_fingerprint=None,
            process_group_id=None,
            status=status,
            exit_code=0 if status == "succeeded" else 1,
            stop_requested=status == "stopped",
            stdout_path=str(run_dir / "stdout.log"),
            stderr_path=str(run_dir / "stderr.log"),
            result_path=str(run_dir / "result.json"),
            created_at=now,
            started_at=now,
            finished_at=now if status != "running" else None,
            updated_at=now,
        )

    def _install_run(self, status: str, run_id: str = "run-success") -> None:
        run = self._run(status, run_id)
        save_runner_registry(
            registry_path(self.settings, self.execution_root),
            RunnerRegistry(self.settings.repository_id, (run,)),
        )

    @patch("engineering_graph.validation.status_supervisor_jobs", return_value=())
    def test_success_executes_frozen_commands_and_persists_record(self, _supervisors) -> None:
        record = run_validation(self.settings, self.task_id, root_override=self.execution_root)
        self.assertEqual(record.status, "passed")
        self.assertTrue(record.workspace_stable)
        self.assertEqual(len(record.commands), 2)
        self.assertTrue(all(result.exit_code == 0 for result in record.commands))
        self.assertIn("first-ok", Path(record.commands[0].stdout_path).read_text(encoding="utf-8"))
        records = status_validations(self.settings, task_id=self.task_id, root_override=self.execution_root)
        self.assertEqual([item.validation_id for item in records], [record.validation_id])
        leases = load_registry(self.execution_root / "leases.json", expected_repository=self.settings.repository_id)
        self.assertIsNotNone(active_lease(leases, self.task_id))

    @patch("engineering_graph.validation.status_supervisor_jobs", return_value=())
    def test_first_failure_stops_later_commands(self, _supervisors) -> None:
        marker = self.worktree / "should-not-exist.txt"
        self._install_allocation(
            (
                f"{sys.executable} -c \"import sys; print('boom'); sys.exit(7)\"",
                f"{sys.executable} -c \"from pathlib import Path; Path('{marker.name}').write_text('bad')\"",
            )
        )
        record = run_validation(self.settings, self.task_id, root_override=self.execution_root)
        self.assertEqual(record.status, "failed")
        self.assertEqual(len(record.commands), 1)
        self.assertEqual(record.commands[0].exit_code, 7)
        self.assertFalse(marker.exists())

    @patch("engineering_graph.validation.status_supervisor_jobs", return_value=())
    def test_unsuccessful_latest_v5_run_is_rejected_before_execution(self, _supervisors) -> None:
        self._install_run("failed")
        with self.assertRaisesRegex(ValidationError, "must be succeeded"):
            run_validation(self.settings, self.task_id, root_override=self.execution_root)
        self.assertFalse((self.execution_root / "validation").exists())

    def test_active_supervisor_run_id_mismatch_fails_closed(self) -> None:
        now = "2026-09-15T00:00:00+00:00"
        job = SupervisorJob(
            job_id="job-1",
            repository=self.settings.repository_id,
            source_revision=self.revision,
            spec_id="SPEC-015-AGENT-VALIDATOR",
            agent="codex",
            manifest_path="/tmp/manifest.json",
            wave=1,
            argv=(sys.executable, "-c", "pass"),
            stdin_handoff=False,
            max_parallel=1,
            max_attempts=1,
            status="active",
            tasks=(
                SupervisorTask(
                    task_id=self.task_id,
                    status="running",
                    attempts=1,
                    run_ids=("other-run",),
                    last_run_status="running",
                ),
            ),
            created_at=now,
            updated_at=now,
        )
        with patch("engineering_graph.validation.status_supervisor_jobs", return_value=(job,)):
            with self.assertRaisesRegex(ValidationError, "ownership mismatch"):
                run_validation(self.settings, self.task_id, root_override=self.execution_root)

    @patch("engineering_graph.validation.status_supervisor_jobs", return_value=())
    def test_workspace_mutation_by_validation_fails_overall_record(self, _supervisors) -> None:
        self._install_allocation(
            (f"{sys.executable} -c \"from pathlib import Path; Path('mutation.txt').write_text('changed')\"",)
        )
        record = run_validation(self.settings, self.task_id, root_override=self.execution_root)
        self.assertEqual(record.commands[0].status, "passed")
        self.assertFalse(record.workspace_stable)
        self.assertEqual(record.status, "failed")


if __name__ == "__main__":
    unittest.main()
