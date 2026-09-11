from __future__ import annotations

import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from engineering_graph.config import ContextBudget, GraphSettings, Neo4jSettings
from engineering_graph.execution import build_execution_manifest
from engineering_graph.leases import active_lease, load_registry
from engineering_graph.orchestrator import (
    prepare_execution,
    release_execution,
    select_manifest_tasks,
)
from engineering_graph.planner import ExecutionPlan
from engineering_graph.worktrees import current_revision, list_worktrees


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def init_repo(root: Path) -> str:
    git(root, "init")
    git(root, "config", "user.email", "graph-tests@example.invalid")
    git(root, "config", "user.name", "Engineering Graph Tests")
    (root / "README.md").write_text("# fixture\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-m", "fixture")
    return current_revision(root)


class FakeContextStore:
    def __init__(self, revision: str) -> None:
        self.revision = revision

    def query_file(self, filename: str, parameters: dict[str, object]):
        if filename != "agent-context.cypher":
            raise AssertionError(f"Unexpected query: {filename}")
        task_id = str(parameters["taskId"])
        return [
            {
                "sourceRevision": self.revision,
                "task": {
                    "canonicalId": task_id,
                    "title": "Fixture task",
                    "sourcePath": "specs/011-execution-graph/tasks.md",
                    "sourceRevision": self.revision,
                },
                "spec": {
                    "canonicalId": "SPEC-011-EXECUTION-GRAPH",
                    "title": "Execution Graph",
                    "sourcePath": "specs/011-execution-graph/spec.md",
                    "sourceRevision": self.revision,
                },
                "requirements": [],
                "adrs": [],
                "dependencies": [],
                "code": [],
                "tests": [],
                "pullRequests": [],
            }
        ]


def settings(repo_root: Path) -> GraphSettings:
    return GraphSettings(
        tool_root=repo_root / "engineering-graph",
        repo_root=repo_root,
        repository_id="example/project",
        neo4j=Neo4jSettings("bolt://unused", "neo4j", "unused", "neo4j"),
        context=ContextBudget(3, 80, 65536),
        validation_rules={},
        historical_spec_prefixes=(),
        specs_glob="",
        tasks_name="tasks.md",
        plans_name="plan.md",
        adr_glob="",
        prune_stale=True,
    )


def manifest(revision: str):
    plan = ExecutionPlan(
        ready=("SPEC-011-EXECUTION-GRAPH:T001",),
        blocked=(),
        cycles=(),
        conflicts=(),
        waves=(("SPEC-011-EXECUTION-GRAPH:T001",),),
    )
    return build_execution_manifest(
        plan,
        repository="example/project",
        source_revision=revision,
        spec_id="SPEC-011-EXECUTION-GRAPH",
        agent="codex",
        generated_at="2026-09-11T10:00:00+00:00",
    )


class OrchestratorTests(unittest.TestCase):
    def test_task_selection_cannot_cross_waves(self) -> None:
        plan = ExecutionPlan(
            ready=("A", "B"),
            blocked=(("C", ("A",)),),
            cycles=(),
            conflicts=(),
            waves=(("A", "B"), ("C",)),
        )
        value = build_execution_manifest(
            plan,
            repository="example/project",
            source_revision="abc",
            spec_id="SPEC",
            agent="codex",
        )
        self.assertEqual(select_manifest_tasks(value, wave=1), ("A", "B"))
        self.assertEqual(select_manifest_tasks(value, task_ids=("B",)), ("B",))
        with self.assertRaisesRegex(ValueError, "one execution wave"):
            select_manifest_tasks(value, task_ids=("A", "C"))

    def test_prepare_dry_run_has_no_worktree_or_lease_mutation(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            revision = init_repo(root)
            state_root = Path(temp) / "execution-state"
            result = prepare_execution(
                FakeContextStore(revision),
                settings(root),
                manifest(revision),
                wave=1,
                root_override=state_root,
                dry_run=True,
            )
            self.assertTrue(result.dry_run)
            self.assertEqual(result.allocations[0].lease_status, "planned")
            self.assertFalse((state_root / "leases.json").exists())
            self.assertEqual(len(list_worktrees(root)), 1)

    def test_prepare_and_release_real_worktree(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            revision = init_repo(root)
            state_root = Path(temp) / "execution-state"
            result = prepare_execution(
                FakeContextStore(revision),
                settings(root),
                manifest(revision),
                wave=1,
                root_override=state_root,
            )
            self.assertFalse(result.dry_run)
            allocation = result.allocations[0]
            self.assertEqual(allocation.lease_status, "active")
            self.assertTrue(Path(allocation.worktree_path).exists())
            self.assertTrue(Path(allocation.context_path).exists())
            self.assertTrue(Path(allocation.handoff_path).exists())

            context_payload = json.loads(Path(allocation.context_path).read_text(encoding="utf-8"))
            self.assertEqual(context_payload["freshness"], "current")
            self.assertEqual(context_payload["sourceRevision"], revision)
            handoff = Path(allocation.handoff_path).read_text(encoding="utf-8")
            self.assertIn("specs/011-execution-graph/tasks.md", handoff)
            self.assertIn("specs/011-execution-graph/spec.md", handoff)
            self.assertIn(allocation.task_id, handoff)

            registry = load_registry(
                state_root / "leases.json",
                expected_repository="example/project",
            )
            self.assertIsNotNone(active_lease(registry, allocation.task_id))
            self.assertEqual(len(list_worktrees(root)), 2)

            released = release_execution(
                settings(root),
                allocation.task_id,
                root_override=state_root,
                remove=True,
            )
            self.assertEqual(released.lease_status, "released")
            self.assertFalse(Path(allocation.worktree_path).exists())
            self.assertEqual(len(list_worktrees(root)), 1)

    def test_stale_manifest_fails_before_mutation(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            original = init_repo(root)
            stale = manifest(original)
            (root / "next.txt").write_text("next\n", encoding="utf-8")
            git(root, "add", "next.txt")
            git(root, "commit", "-m", "next")
            state_root = Path(temp) / "execution-state"
            with self.assertRaisesRegex(RuntimeError, "manifest is stale"):
                prepare_execution(
                    FakeContextStore(original),
                    settings(root),
                    stale,
                    wave=1,
                    root_override=state_root,
                    dry_run=True,
                )
            self.assertFalse((state_root / "leases.json").exists())
            self.assertEqual(len(list_worktrees(root)), 1)


if __name__ == "__main__":
    unittest.main()
