from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from engineering_graph.config import ContextBudget, GraphSettings, Neo4jSettings
from engineering_graph.execution import planned_allocation
from engineering_graph.runner import (
    AgentRun,
    RunnerError,
    RunnerRegistry,
    expand_command,
    load_runner_registry,
    refresh_run,
    save_runner_registry,
)


class AgentRunnerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.settings = GraphSettings(
            tool_root=self.root / "engineering-graph",
            repo_root=self.root,
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
        self.run_dir = self.root / "runs" / "fixture"
        self.run_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(self, **overrides: object) -> AgentRun:
        values: dict[str, object] = {
            "run_id": "fixture",
            "repository": "example/runner",
            "task_id": "SPEC-013-AGENT-RUNNER:T053",
            "spec_id": "SPEC-013-AGENT-RUNNER",
            "source_revision": "abc123",
            "agent": "codex",
            "branch": "exec/spec-013-agent-runner-t053",
            "worktree_path": str(self.root / "worktree"),
            "handoff_path": str(self.root / "handoff.md"),
            "context_path": str(self.root / "context.json"),
            "argv": ("python", "-c", "print('ok')"),
            "stdin_handoff": False,
            "pid": 424242,
            "process_fingerprint": "linux-proc:424242:1",
            "process_group_id": 424242,
            "status": "running",
            "exit_code": None,
            "stop_requested": False,
            "stdout_path": str(self.run_dir / "stdout.log"),
            "stderr_path": str(self.run_dir / "stderr.log"),
            "result_path": str(self.run_dir / "result.json"),
            "created_at": "2026-09-13T00:00:00+00:00",
            "started_at": "2026-09-13T00:00:00+00:00",
            "finished_at": None,
            "updated_at": "2026-09-13T00:00:00+00:00",
        }
        values.update(overrides)
        return AgentRun(**values)  # type: ignore[arg-type]

    def test_registry_roundtrip_preserves_versioned_run_contract(self) -> None:
        path = self.root / "registry.json"
        original = RunnerRegistry("example/runner", (self._run(),))
        save_runner_registry(path, original)
        loaded = load_runner_registry(path, expected_repository="example/runner")
        self.assertEqual(loaded.to_dict(), original.to_dict())
        self.assertEqual(loaded.registry_version, "1")
        self.assertEqual(loaded.runs[0].run_version, "1")

    def test_malformed_registry_fails_closed(self) -> None:
        path = self.root / "registry.json"
        path.write_text("{not-json", encoding="utf-8")
        with self.assertRaises(RunnerError):
            load_runner_registry(path, expected_repository="example/runner")

    def test_duplicate_nonterminal_registry_is_invalid(self) -> None:
        path = self.root / "registry.json"
        first = self._run(run_id="first")
        second = self._run(run_id="second")
        with self.assertRaises(RunnerError):
            save_runner_registry(path, RunnerRegistry("example/runner", (first, second)))

    def test_command_placeholders_are_token_local_and_do_not_invoke_shell(self) -> None:
        allocation = planned_allocation(
            repository="example/runner",
            task_id="SPEC-013-AGENT-RUNNER:T055",
            spec_id="SPEC-013-AGENT-RUNNER",
            source_revision="deadbeef",
            agent="codex",
            branch="exec/spec-013-agent-runner-t055",
            worktree_path="/tmp/work tree",
            context_path="/tmp/context.json",
            handoff_path="/tmp/handoff.md",
        )
        expanded = expand_command(
            [
                "printf",
                "{task_id}",
                "{worktree}",
                "literal;echo-not-a-shell-command",
            ],
            allocation,
        )
        self.assertEqual(expanded[1], allocation.task_id)
        self.assertEqual(expanded[2], allocation.worktree_path)
        self.assertEqual(expanded[3], "literal;echo-not-a-shell-command")
        self.assertEqual(len(expanded), 4)

    def test_vanished_process_reconciles_to_orphaned(self) -> None:
        candidate = 999999
        while Path(f"/proc/{candidate}").exists():
            candidate += 1
        run = self._run(
            pid=candidate,
            process_fingerprint=f"linux-proc:{candidate}:1",
        )
        refreshed = refresh_run(self.settings, run)
        self.assertEqual(refreshed.status, "orphaned")
        self.assertIsNotNone(refreshed.finished_at)

    def test_exit_result_reconciles_success_without_task_semantics(self) -> None:
        run = self._run()
        Path(run.result_path).write_text(
            json.dumps(
                {
                    "resultVersion": "1",
                    "runId": run.run_id,
                    "exitCode": 0,
                    "finishedAt": "2026-09-13T00:00:01+00:00",
                }
            ),
            encoding="utf-8",
        )
        refreshed = refresh_run(self.settings, run)
        self.assertEqual(refreshed.status, "succeeded")
        self.assertEqual(refreshed.exit_code, 0)
        self.assertEqual(refreshed.task_id, run.task_id)


if __name__ == "__main__":
    unittest.main()
