from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from engineering_graph.execution import planned_allocation
from engineering_graph.leases import (
    LeaseCollisionError,
    LeaseRegistryError,
    acquire_lease,
    active_lease,
    load_registry,
    release_lease,
)


def allocation(task_id: str, path: Path, *, branch: str | None = None):
    return planned_allocation(
        repository="example/project",
        task_id=task_id,
        spec_id="SPEC-011",
        source_revision="abc123",
        agent="codex",
        branch=branch or f"exec/{task_id.lower().replace(':', '-')}",
        worktree_path=str(path),
        context_path=str(path.parent / "context.json"),
        handoff_path=str(path.parent / "codex.md"),
        validation_commands=("git diff --check",),
        now="2026-09-11T10:00:00+00:00",
    )


class LeaseTests(unittest.TestCase):
    def test_acquire_collision_release(self) -> None:
        with TemporaryDirectory() as temp:
            registry_path = Path(temp) / "leases.json"
            first = allocation("SPEC-011:T001", Path(temp) / "worktree-1")
            active = acquire_lease(registry_path, first)
            self.assertEqual(active.lease_status, "active")
            registry = load_registry(registry_path, expected_repository="example/project")
            self.assertEqual(active_lease(registry, "SPEC-011:T001"), active)

            with self.assertRaisesRegex(LeaseCollisionError, "already has an active lease"):
                acquire_lease(registry_path, first)

            released = release_lease(
                registry_path,
                repository="example/project",
                task_id="SPEC-011:T001",
            )
            self.assertEqual(released.lease_status, "released")
            registry = load_registry(registry_path, expected_repository="example/project")
            self.assertIsNone(active_lease(registry, "SPEC-011:T001"))

            reacquired = acquire_lease(registry_path, first)
            self.assertEqual(reacquired.lease_status, "active")

    def test_branch_and_path_collisions_are_rejected(self) -> None:
        with TemporaryDirectory() as temp:
            registry_path = Path(temp) / "leases.json"
            base = allocation("SPEC-011:T001", Path(temp) / "shared", branch="exec/shared")
            acquire_lease(registry_path, base)
            with self.assertRaises(LeaseCollisionError):
                acquire_lease(
                    registry_path,
                    allocation("SPEC-011:T002", Path(temp) / "other", branch="exec/shared"),
                )
            with self.assertRaises(LeaseCollisionError):
                acquire_lease(
                    registry_path,
                    allocation("SPEC-011:T003", Path(temp) / "shared", branch="exec/other"),
                )

    def test_malformed_registry_fails_closed(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "leases.json"
            path.write_text("{not-json", encoding="utf-8")
            with self.assertRaisesRegex(LeaseRegistryError, "not valid JSON"):
                load_registry(path, expected_repository="example/project")

    def test_repository_mismatch_fails_closed(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "leases.json"
            acquire_lease(
                path,
                allocation("SPEC-011:T001", Path(temp) / "worktree"),
            )
            with self.assertRaisesRegex(LeaseRegistryError, "repository mismatch"):
                load_registry(path, expected_repository="another/project")


if __name__ == "__main__":
    unittest.main()
