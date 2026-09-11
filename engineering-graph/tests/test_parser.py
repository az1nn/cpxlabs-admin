from __future__ import annotations

import unittest

from engineering_graph.config import normalize_repository_id
from engineering_graph.parser import (
    canonical_adr_id,
    canonical_requirement_id,
    canonical_spec_id,
    canonical_task_id,
    extract_paths,
    parse_frontmatter,
    parse_requirements,
    parse_tasks,
)


class ParserTests(unittest.TestCase):
    def test_frontmatter_is_optional_and_preserves_body_line_offset(self) -> None:
        parsed = parse_frontmatter(
            """---
graph:
  enforced: true
---
# Example
Body
"""
        )
        self.assertEqual(parsed.metadata["graph"]["enforced"], True)
        self.assertEqual(parsed.body_start_line, 5)
        self.assertTrue(parsed.body.startswith("# Example"))

    def test_canonical_ids_namespace_local_spec_kit_identifiers(self) -> None:
        spec = canonical_spec_id("009-graph-engineering-control-plane")
        self.assertEqual(spec, "SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE")
        self.assertEqual(
            canonical_requirement_id(spec, "FR-001"),
            "SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE:FR-001",
        )
        self.assertEqual(
            canonical_task_id(spec, "T001"),
            "SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE:T001",
        )
        self.assertEqual(canonical_adr_id("0017-graph-engineering.md"), "ADR-0017")

    def test_requirements_extract_functional_and_success_criteria(self) -> None:
        requirements = parse_requirements(
            """- **FR-001**: The system MUST preserve Git authority.
- **SC-001**: Two syncs yield the same graph.
"""
        )
        self.assertEqual([item.source_id for item in requirements], ["FR-001", "SC-001"])
        self.assertEqual(requirements[0].kind, "functional")
        self.assertTrue(requirements[0].critical)
        self.assertEqual(requirements[1].kind, "success_criterion")

    def test_tasks_extract_status_phase_parallel_story_dependencies_and_paths(self) -> None:
        tasks = parse_tasks(
            """## Phase 1 — Core
- [x] T001 [P] [US1] Build parser (`depends: T002,T003`) `apps/api/src/app.ts` `tests/parser.test.ts`
"""
        )
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task.source_id, "T001")
        self.assertEqual(task.status, "done")
        self.assertEqual(task.phase, "Phase 1 — Core")
        self.assertTrue(task.parallel)
        self.assertEqual(task.user_story, "US1")
        self.assertEqual(task.dependencies, ("T002", "T003"))
        self.assertEqual(task.paths, ("apps/api/src/app.ts", "tests/parser.test.ts"))

    def test_path_extraction_is_deterministic_and_ignores_urls(self) -> None:
        paths = extract_paths(
            "Change `apps/web/src/main.tsx`, tests/e2e/auth.spec.ts and https://example.com/a.ts"
        )
        self.assertEqual(paths, ("apps/web/src/main.tsx", "tests/e2e/auth.spec.ts"))

    def test_repository_remote_normalization(self) -> None:
        self.assertEqual(
            normalize_repository_id("git@github.com:az1nn/cpxlabs-admin.git"),
            "az1nn/cpxlabs-admin",
        )
        self.assertEqual(
            normalize_repository_id("https://github.com/az1nn/cpxlabs-admin.git"),
            "az1nn/cpxlabs-admin",
        )


if __name__ == "__main__":
    unittest.main()
