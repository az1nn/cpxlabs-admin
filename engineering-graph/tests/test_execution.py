from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from engineering_graph.execution import (
    ExecutionManifest,
    build_execution_manifest,
    load_execution_manifest,
    validate_execution_manifest,
    write_execution_manifest,
)
from engineering_graph.planner import ExecutionPlan, TaskConflict


class ExecutionManifestTests(unittest.TestCase):
    def plan(self) -> ExecutionPlan:
        return ExecutionPlan(
            ready=("SPEC-011:T001", "SPEC-011:T002"),
            blocked=(("SPEC-011:T003", ("SPEC-011:T001",)),),
            cycles=(),
            conflicts=(TaskConflict("SPEC-011:T001", "SPEC-011:T002", ("src/shared.ts",)),),
            waves=(("SPEC-011:T001",), ("SPEC-011:T002", "SPEC-011:T003")),
        )

    def test_manifest_semantics_ignore_generated_timestamp(self) -> None:
        first = build_execution_manifest(
            self.plan(),
            repository="example/project",
            source_revision="abc123",
            spec_id="SPEC-011",
            agent="codex",
            generated_at="2026-09-11T10:00:00+00:00",
        )
        second = build_execution_manifest(
            self.plan(),
            repository="example/project",
            source_revision="abc123",
            spec_id="SPEC-011",
            agent="codex",
            generated_at="2026-09-11T11:00:00+00:00",
        )
        self.assertEqual(first.semantic_json(), second.semantic_json())

    def test_manifest_roundtrip(self) -> None:
        manifest = build_execution_manifest(
            self.plan(),
            repository="example/project",
            source_revision="abc123",
            spec_id="SPEC-011",
            agent="claude",
            generated_at="2026-09-11T10:00:00+00:00",
        )
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            write_execution_manifest(manifest, path)
            loaded = load_execution_manifest(path)
        self.assertEqual(manifest, loaded)

    def test_invalid_wave_indexes_fail_closed(self) -> None:
        manifest = build_execution_manifest(
            self.plan(),
            repository="example/project",
            source_revision="abc123",
            spec_id="SPEC-011",
            agent="codex",
        )
        payload = manifest.to_dict()
        payload["waves"][0]["index"] = 2
        malformed = ExecutionManifest.from_dict(payload)
        with self.assertRaisesRegex(ValueError, "wave indexes"):
            validate_execution_manifest(malformed)

    def test_unsupported_agent_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported agent"):
            build_execution_manifest(
                self.plan(),
                repository="example/project",
                source_revision="abc123",
                spec_id="SPEC-011",
                agent="unknown",
            )

    def test_manifest_json_shape(self) -> None:
        manifest = build_execution_manifest(
            self.plan(),
            repository="example/project",
            source_revision="abc123",
            spec_id="SPEC-011",
            agent="codex",
            generated_at="2026-09-11T10:00:00+00:00",
        )
        payload = json.loads(json.dumps(manifest.to_dict()))
        self.assertEqual(payload["manifestVersion"], "1")
        self.assertEqual(payload["waves"][0], {"index": 1, "tasks": ["SPEC-011:T001"]})


if __name__ == "__main__":
    unittest.main()
