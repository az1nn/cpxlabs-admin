from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from engineering_graph.execution import planned_allocation
from engineering_graph.leases import acquire_lease, active_lease, load_registry
from engineering_graph.worktrees import (
    branch_name_for_task,
    current_revision,
    ensure_worktree,
    worktree_path_for_task,
)


@unittest.skipUnless(Path("/proc/self/stat").exists(), "Linux process-group/fingerprint semantics required")
class AgentRunnerForceCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        subprocess.run(["git", "init"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "runner-force@example.test"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Runner Force Test"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/example/runner-force.git"],
            cwd=self.repo,
            check=True,
        )
        (self.repo / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=self.repo, check=True, capture_output=True)

        self.execution_root = self.repo / ".execution-test"
        self.task_id = "SPEC-013-AGENT-RUNNER:T062"
        self.revision = current_revision(self.repo)
        branch = branch_name_for_task(self.task_id)
        worktree = worktree_path_for_task(self.execution_root, self.task_id)
        ensure_worktree(
            self.repo,
            path=worktree,
            branch=branch,
            source_revision=self.revision,
        )
        context_dir = self.execution_root / "contexts" / "force"
        context_dir.mkdir(parents=True, exist_ok=True)
        context = context_dir / "context.json"
        handoff = context_dir / "codex.md"
        context.write_text('{"fixture": true}\n', encoding="utf-8")
        handoff.write_text("FORCE_HANDOFF\n", encoding="utf-8")
        allocation = planned_allocation(
            repository="example/runner-force",
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
        self.process_group_id: int | None = None

    def tearDown(self) -> None:
        if self.process_group_id is not None:
            try:
                os.killpg(self.process_group_id, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        self.temporary.cleanup()

    def _entry(self, *args: str, timeout: float = 10.0) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["GRAPH_REPOSITORY_ID"] = "example/runner-force"
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "engineering_graph.runner_entry",
                "--repo-root",
                str(self.repo),
                *args,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=environment,
        )

    def test_force_stop_kills_sigterm_ignoring_fixture_and_preserves_lease(self) -> None:
        ignore_term = (
            "import signal,time; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "time.sleep(30)"
        )
        started = self._entry(
            "runner-start",
            self.task_id,
            "--execution-root",
            str(self.execution_root),
            "--json",
            "--command",
            sys.executable,
            "-c",
            ignore_term,
        )
        self.assertEqual(started.returncode, 0, started.stderr)
        payload = json.loads(started.stdout)
        self.process_group_id = payload.get("processGroupId")
        self.assertEqual(payload["status"], "running")

        time.sleep(0.2)
        stopped = self._entry(
            "runner-stop",
            self.task_id,
            "--execution-root",
            str(self.execution_root),
            "--timeout",
            "1.0",
            "--force",
            "--json",
        )
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        stopped_payload = json.loads(stopped.stdout)
        self.assertEqual(stopped_payload["status"], "stopped")

        leases = load_registry(
            self.execution_root / "leases.json",
            expected_repository="example/runner-force",
        )
        self.assertIsNotNone(active_lease(leases, self.task_id))
        self.process_group_id = None


if __name__ == "__main__":
    unittest.main()
