from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import unittest

from engineering_graph.config import load_settings
from engineering_graph.validator import has_errors, validate_graph


REPO_ROOT = Path(__file__).resolve().parents[2]


class FakeStore:
    def __init__(self, *, cycle: bool = False) -> None:
        self.cycle = cycle

    def run(self, query: str, parameters: dict[str, object] | None = None):
        if "coalesce(s.enforced" in query:
            return [
                {
                    "entity": "SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE",
                    "specId": "SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE",
                    "sourcePath": "specs/009-graph-engineering-control-plane/spec.md",
                }
            ]
        if "status: 'done'" in query and "IMPLEMENTED_BY" in query:
            return [
                {
                    "entity": "SPEC-001-FOUNDATION:T001",
                    "specId": "SPEC-001-FOUNDATION",
                    "sourcePath": "specs/001-foundation/tasks.md",
                }
            ]
        if "status: 'done'" in query and "VALIDATED_BY" in query:
            return []
        if "critical: true" in query:
            return []
        if "MATCH (a:ADR" in query:
            return [{"entity": "ADR-0099", "sourcePath": "docs/adr/0099-unused.md"}]
        if "MATCH (t:Task" in query:
            if not self.cycle:
                return []
            return [
                {
                    "canonicalId": "SPEC-009:X",
                    "status": "pending",
                    "priority": 1,
                    "dependencies": ["SPEC-009:Y"],
                    "artifacts": [],
                },
                {
                    "canonicalId": "SPEC-009:Y",
                    "status": "pending",
                    "priority": 2,
                    "dependencies": ["SPEC-009:X"],
                    "artifacts": [],
                },
            ]
        raise AssertionError(f"Unexpected validator query: {query}")


class ValidatorTests(unittest.TestCase):
    def settings(self):
        settings = load_settings(repo_root=REPO_ROOT)
        rules = dict(settings.validation_rules)
        rules.update(
            {
                "enforced-spec-no-task": "error",
                "completed-task-no-code": "error",
                "completed-task-no-test": "warning",
                "critical-requirement-no-test": "warning",
                "adr-no-consumer": "warning",
                "task-dependency-cycle": "error",
            }
        )
        return replace(settings, validation_rules=rules)

    def test_errors_warnings_and_historical_downgrade(self) -> None:
        results = validate_graph(FakeStore(), self.settings())
        by_rule = {result.rule: result for result in results}

        self.assertEqual(by_rule["enforced-spec-no-task"].severity, "error")
        self.assertEqual(by_rule["completed-task-no-code"].severity, "warning")
        self.assertEqual(by_rule["adr-no-consumer"].severity, "warning")
        self.assertTrue(has_errors(results))

    def test_dependency_cycle_is_error(self) -> None:
        results = validate_graph(FakeStore(cycle=True), self.settings())
        cycle = next(result for result in results if result.rule == "task-dependency-cycle")

        self.assertEqual(cycle.severity, "error")
        self.assertIn("SPEC-009:X", cycle.message)
        self.assertIn("SPEC-009:Y", cycle.message)

    def test_off_rule_is_suppressed(self) -> None:
        settings = self.settings()
        rules = dict(settings.validation_rules)
        rules["adr-no-consumer"] = "off"
        results = validate_graph(FakeStore(), replace(settings, validation_rules=rules))

        self.assertFalse(any(result.rule == "adr-no-consumer" for result in results))


if __name__ == "__main__":
    unittest.main()
