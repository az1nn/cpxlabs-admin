from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from engineering_graph.config import ContextBudget, GraphSettings, Neo4jSettings
from engineering_graph.execution import planned_allocation
from engineering_graph.leases import acquire_lease, active_lease, load_registry
from engineering_graph.runner import (
    AgentRun,
    RunnerCollisionError,
    RunnerRegistry,
    latest_run,
    process_alive,
    process_fingerprint,
    read_run_logs,
    registry_path,
    save_runner_registry,
    start_run,
    status_runs,
    stop_run,
)
from engineering_graph.worktrees import (
    branch_name_for_task,
    current_revision,
    ensure_worktree,
    worktree_path_for_task,
)


class AgentRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        subprocess.run(["git", "init"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "runner@example.test"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Runner Test"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/example/runner.git"],
            cwd=self.repo,
            check=True,
        )
        (self.repo / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=self.repo, check=True, capture_output=True)

        self.execution_root = self.repo / ".execution-test"
        self.task_id = "SPEC-013-AGENT-RUNNER:T057"
        self.settings = GraphSettings(
            tool_root=self.repo / "engineering-graph",
            repo_root=self.repo,
            repository_id="example/runner",
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
        branch = branch_name_for_task(self.task_id)
        worktree = worktree_path_for_task(self.execution_root, self.task_id)
        ensure_worktree(
            self.repo,
            path=worktree,
            branch=branch,
            source_revision=self.revision,
        )
        context_dir = self.execution_root / "contexts" / "spec-013-agent-runner-t057"
        context_dir.mkdir(parents=True, exist_ok=True)
        context = context_dir / "context.json"
        handoff = context_dir / "codex.md"
        context.write_text('{"fixture": true}\n', encoding="utf-8")
        handoff.write_text("RUNNER_HANDOFF_FIXTURE\n", encoding="utf-8")
        allocation = planned_allocation(
            repository=self.settings.repository_id,
            task_id=self.task_id,
            spec_id="SPEC-013-AGENT-RUNNER",
            source_revision=self.revision,
            agent="codex",
            branch=branch,
            worktree_path=str(worktree),
            context_path=str(context),
            handoff_path=str(handoff),
        )
        acquire_lease(self.execution_root / "leases.json", allocation)
        self.spawned_groups: set[int] = set()

    def tearDown(self) -> None:
        for pgid in self.spawned_groups:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        self.temporary.cleanup()

    def _track(self, run: AgentRun) -> AgentRun:
        if run.process_group_id is not None:
            self.spawned_groups.add(run.process_group_id)
        return run

    def _wait_terminal(self, timeout: float = 5.0) -> AgentRun:
        deadline = time.monotonic() + timeout
        current: AgentRun | None = None
        while time.monotonic() < deadline:
            values = status_runs(
                self.settings,
                task_id=self.task_id,
                root_override=self.execution_root,
            )
            current = latest_run(RunnerRegistry(self.settings.repository_id, values), self.task_id)
            if current is not None and current.terminal:
                return current
            time.sleep(0.05)
        self.fail(f"runner did not become terminal: {current}")

    def test_successful_run_uses_worktree_handoff_and_logs(self) -> None:
        code = (
            "import os,sys; "
            "data=sys.stdin.read().strip(); "
            "print('cwd='+os.getcwd()); "
            "print('handoff='+data); "
            "print('stderr-fixture', file=sys.stderr)"
        )
        run = self._track(
            start_run(
                self.settings,
                self.task_id,
                [sys.executable, "-c", code],
                stdin_handoff=True,
                root_override=self.execution_root,
            )
        )
        self.assertEqual(run.status, "running")
        finished = self._wait_terminal()
        self.assertEqual(finished.status, "succeeded")
        self.assertEqual(finished.exit_code, 0)
        logs = read_run_logs(
            self.settings,
            self.task_id,
            stream="both",
            root_override=self.execution_root,
        )
        self.assertIn(f"cwd={Path(run.worktree_path)}", logs["stdout"])
        self.assertIn("handoff=RUNNER_HANDOFF_FIXTURE", logs["stdout"])
        self.assertIn("stderr-fixture", logs["stderr"])
        leases = load_registry(
            self.execution_root / "leases.json",
            expected_repository=self.settings.repository_id,
        )
        self.assertIsNotNone(active_lease(leases, self.task_id))

    def test_nonzero_exit_is_failed_without_releasing_lease(self) -> None:
        self._track(
            start_run(
                self.settings,
                self.task_id,
                [sys.executable, "-c", "import sys; sys.exit(7)"],
                root_override=self.execution_root,
            )
        )
        finished = self._wait_terminal()
        self.assertEqual(finished.status, "failed")
        self.assertEqual(finished.exit_code, 7)
        leases = load_registry(
            self.execution_root / "leases.json",
            expected_repository=self.settings.repository_id,
        )
        self.assertIsNotNone(active_lease(leases, self.task_id))

    def test_duplicate_running_task_is_rejected_then_can_be_stopped(self) -> None:
        run = self._track(
            start_run(
                self.settings,
                self.task_id,
                [sys.executable, "-c", "import time; time.sleep(30)"],
                root_override=self.execution_root,
            )
        )
        with self.assertRaises(RunnerCollisionError):
            start_run(
                self.settings,
                self.task_id,
                [sys.executable, "-c", "print('duplicate')"],
                root_override=self.execution_root,
            )
        stopped = stop_run(
            self.settings,
            self.task_id,
            root_override=self.execution_root,
            timeout_seconds=2.0,
            force=True,
        )
        self.assertEqual(stopped.status, "stopped")
        if run.process_group_id is not None:
            self.spawned_groups.discard(run.process_group_id)

    @unittest.skipUnless(Path("/proc/self/stat").exists(), "Linux /proc process identity required")
    def test_process_fingerprint_mismatch_never_signals_current_pid(self) -> None:
        fingerprint = process_fingerprint(os.getpid())
        self.assertIsNotNone(fingerprint)
        run_dir = self.execution_root / "runs" / "identity-mismatch"
        run_dir.mkdir(parents=True, exist_ok=True)
        now = "2026-01-01T00:00:00+00:00"
        run = AgentRun(
            run_id="identity-mismatch",
            repository=self.settings.repository_id,
            task_id="SPEC-013-AGENT-RUNNER:T056",
            spec_id="SPEC-013-AGENT-RUNNER",
            source_revision=self.revision,
            agent="codex",
            branch="exec/identity-mismatch",
            worktree_path=str(self.repo),
            handoff_path=str(run_dir / "handoff.md"),
            context_path=str(run_dir / "context.json"),
            argv=(sys.executable, "-c", "pass"),
            stdin_handoff=False,
            pid=os.getpid(),
            process_fingerprint="linux-proc:wrong",
            process_group_id=None,
            status="running",
            exit_code=None,
            stop_requested=False,
            stdout_path=str(run_dir / "stdout.log"),
            stderr_path=str(run_dir / "stderr.log"),
            result_path=str(run_dir / "result.json"),
            created_at=now,
            started_at=now,
            finished_at=None,
            updated_at=now,
        )
        save_runner_registry(
            registry_path(self.settings, self.execution_root),
            RunnerRegistry(self.settings.repository_id, (run,)),
        )
        observed = stop_run(
            self.settings,
            run.task_id,
            root_override=self.execution_root,
            timeout_seconds=0.1,
        )
        self.assertEqual(observed.status, "orphaned")
        self.assertTrue(process_alive(os.getpid()))


if __name__ == "__main__":
    unittest.main()
