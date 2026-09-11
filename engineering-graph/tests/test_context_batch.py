from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from engineering_graph.config import ContextBudget, GraphSettings, Neo4jSettings
from engineering_graph.context_batch import generate_context_packages, ready_task_ids, select_task_ids


class FakeStore:
    source_revision = "abc123"

    def query_file(self, filename: str, parameters: dict[str, object]):
        if filename == "ready-tasks.cypher":
            return [
                {"task": "SPEC-010-EXAMPLE:T001", "ready": True, "blockers": []},
                {"task": "SPEC-010-EXAMPLE:T002", "ready": False, "blockers": ["SPEC-010-EXAMPLE:T001"]},
                {"task": "SPEC-010-EXAMPLE:T003", "ready": True, "blockers": []},
            ]
        if filename == "agent-context.cypher":
            task_id = str(parameters["taskId"])
            return [
                {
                    "sourceRevision": self.source_revision,
                    "task": {
                        "canonicalId": task_id,
                        "title": f"Task {task_id}",
                        "sourcePath": "specs/010-example/tasks.md",
                        "sourceRevision": self.source_revision,
                    },
                    "spec": {
                        "canonicalId": "SPEC-010-EXAMPLE",
                        "sourcePath": "specs/010-example/spec.md",
                        "sourceRevision": self.source_revision,
                    },
                    "requirements": [],
                    "adrs": [],
                    "dependencies": [],
                    "code": [
                        {
                            "canonicalId": "engineering-graph/src/engineering_graph/context.py",
                            "path": "engineering-graph/src/engineering_graph/context.py",
                        }
                    ],
                    "tests": [
                        {
                            "canonicalId": "engineering-graph/tests/test_context.py",
                            "path": "engineering-graph/tests/test_context.py",
                        }
                    ],
                    "pullRequests": [],
                }
            ]
        raise AssertionError(f"Unexpected query: {filename}")


class NoReadyTaskStore(FakeStore):
    def query_file(self, filename: str, parameters: dict[str, object]):
        if filename == "ready-tasks.cypher":
            return [
                {"task": "SPEC-010-EXAMPLE:T001", "ready": False, "blockers": []},
                {"task": "SPEC-010-EXAMPLE:T002", "ready": False, "blockers": []},
            ]
        return super().query_file(filename, parameters)


def settings(root: Path) -> GraphSettings:
    return GraphSettings(
        tool_root=root,
        repo_root=root,
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


class ContextBatchTests(unittest.TestCase):
    def test_ready_selection_excludes_blocked_tasks(self) -> None:
        root = Path.cwd()
        selected = ready_task_ids(FakeStore(), settings(root), "SPEC-010-EXAMPLE")
        self.assertEqual(selected, ("SPEC-010-EXAMPLE:T001", "SPEC-010-EXAMPLE:T003"))

    def test_explicit_selection_can_include_blocked_task(self) -> None:
        root = Path.cwd()
        selected = select_task_ids(
            FakeStore(),
            settings(root),
            spec_id=None,
            explicit_task_ids=("SPEC-010-EXAMPLE:T002",),
        )
        self.assertEqual(selected, ("SPEC-010-EXAMPLE:T002",))

    def test_selection_requires_spec_or_task(self) -> None:
        root = Path.cwd()
        with self.assertRaisesRegex(ValueError, "requires --spec"):
            select_task_ids(FakeStore(), settings(root), spec_id=None)

    @patch("engineering_graph.context.current_git_revision", return_value="abc123")
    def test_batch_writes_portable_package_and_both_handoffs(self, _revision) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "packages"
            manifest = generate_context_packages(
                FakeStore(),
                settings(root),
                spec_id="SPEC-010-EXAMPLE",
                output_root=output,
            )
            self.assertEqual(len(manifest.packages), 2)
            self.assertEqual(manifest.source_revision, "abc123")
            manifest_payload = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest_payload["packageCount"], 2)
            self.assertEqual(len(manifest_payload["tasks"]), 2)
            for generated in manifest.packages:
                directory = output / generated.directory
                self.assertTrue((directory / "context.json").exists())
                self.assertTrue((directory / "context.md").exists())
                self.assertTrue((directory / "codex.md").exists())
                self.assertTrue((directory / "claude.md").exists())
                payload = json.loads((directory / "context.json").read_text(encoding="utf-8"))
                self.assertEqual(payload["sourceRevision"], "abc123")
                self.assertEqual(payload["freshness"], "current")
                self.assertEqual(payload["packageVersion"], "1")

    @patch("engineering_graph.context_batch.current_git_revision", return_value="abc123")
    def test_completed_spec_writes_empty_manifest(self, _revision) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "packages"
            manifest = generate_context_packages(
                NoReadyTaskStore(),
                settings(root),
                spec_id="SPEC-010-EXAMPLE",
                output_root=output,
            )

            self.assertEqual(manifest.packages, ())
            self.assertEqual(manifest.source_revision, "abc123")
            payload = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["packageCount"], 0)
            self.assertEqual(payload["tasks"], [])
            self.assertEqual(payload["specId"], "SPEC-010-EXAMPLE")
            self.assertEqual(payload["sourceRevision"], "abc123")

    @patch("engineering_graph.context.current_git_revision", return_value="abc123")
    def test_regeneration_removes_stale_files_and_manifest_is_deterministic(self, _revision) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "packages"
            first = generate_context_packages(
                FakeStore(),
                settings(root),
                explicit_task_ids=("SPEC-010-EXAMPLE:T001",),
                output_root=output,
            )
            task_dir = output / first.packages[0].directory
            stale = task_dir / "stale.tmp"
            stale.write_text("old", encoding="utf-8")
            first_manifest = (output / "manifest.json").read_text(encoding="utf-8")

            generate_context_packages(
                FakeStore(),
                settings(root),
                explicit_task_ids=("SPEC-010-EXAMPLE:T001",),
                output_root=output,
            )
            second_manifest = (output / "manifest.json").read_text(encoding="utf-8")

            self.assertFalse(stale.exists())
            self.assertEqual(first_manifest, second_manifest)


if __name__ == "__main__":
    unittest.main()
