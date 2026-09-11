from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from engineering_graph.config import ContextBudget, GraphSettings, Neo4jSettings
from engineering_graph.context import build_context
from engineering_graph.context_validation import inspect_freshness, load_context_package


class FakeStore:
    source_revision = "rev-a"

    def query_file(self, filename: str, parameters: dict[str, object]):
        return [
            {
                "sourceRevision": self.source_revision,
                "task": {
                    "canonicalId": "SPEC-010-EXAMPLE:T001",
                    "title": "Implement",
                    "sourceRevision": self.source_revision,
                },
                "spec": {
                    "canonicalId": "SPEC-010-EXAMPLE",
                    "title": "Example",
                    "sourceRevision": self.source_revision,
                },
                "requirements": [],
                "adrs": [],
                "dependencies": [],
                "code": [],
                "tests": [],
                "pullRequests": [],
            }
        ]


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


class ContextValidationTests(unittest.TestCase):
    @patch("engineering_graph.context.current_git_revision", return_value="rev-a")
    def package(self, _revision):
        root = Path.cwd()
        return build_context(FakeStore(), settings(root), "SPEC-010-EXAMPLE:T001")

    @patch("engineering_graph.context_validation.current_git_revision", return_value="rev-a")
    def test_strict_current_package_is_valid(self, _revision) -> None:
        package = self.package()
        report = inspect_freshness(
            package,
            Path.cwd(),
            expected_repository="example/project",
            strict=True,
        )
        self.assertEqual(report.status, "current")
        self.assertTrue(report.valid)

    @patch("engineering_graph.context_validation.current_git_revision", return_value="rev-b")
    def test_strict_stale_package_fails_closed(self, _revision) -> None:
        package = self.package()
        report = inspect_freshness(
            package,
            Path.cwd(),
            expected_repository="example/project",
            strict=True,
        )
        self.assertEqual(report.status, "stale")
        self.assertFalse(report.valid)
        self.assertIn("graph revision", report.messages[0].lower())

    @patch("engineering_graph.context_validation.current_git_revision", return_value=None)
    def test_non_strict_unknown_revision_is_reported_without_failure(self, _revision) -> None:
        package = self.package()
        report = inspect_freshness(package, Path.cwd(), strict=False)
        self.assertEqual(report.status, "unknown")
        self.assertTrue(report.valid)

    def test_repository_mismatch_is_invalid_even_when_non_strict(self) -> None:
        package = self.package()
        with patch("engineering_graph.context_validation.current_git_revision", return_value="rev-a"):
            report = inspect_freshness(
                package,
                Path.cwd(),
                expected_repository="other/project",
                strict=False,
            )
        self.assertFalse(report.valid)
        self.assertFalse(report.repository_matches)

    def test_loader_rejects_malformed_package(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "context.json"
            path.write_text(json.dumps({"packageVersion": "1"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing required fields"):
                load_context_package(path)

    def test_loader_rejects_tampered_summary(self) -> None:
        package = self.package()
        payload = package.to_dict()
        payload["summary"]["includedNodes"] = 999
        with TemporaryDirectory() as temp:
            path = Path(temp) / "context.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "includedNodes mismatch"):
                load_context_package(path)

    def test_loader_rejects_tampered_rendered_bytes(self) -> None:
        package = self.package()
        payload = package.to_dict()
        payload["summary"]["renderedBytes"] += 1
        with TemporaryDirectory() as temp:
            path = Path(temp) / "context.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "renderedBytes mismatch"):
                load_context_package(path)

    def test_loader_round_trip(self) -> None:
        package = self.package()
        with TemporaryDirectory() as temp:
            path = Path(temp) / "context.json"
            path.write_text(json.dumps(package.to_dict()), encoding="utf-8")
            restored = load_context_package(path)
        self.assertEqual(restored.semantic_json(), package.semantic_json())


if __name__ == "__main__":
    unittest.main()
