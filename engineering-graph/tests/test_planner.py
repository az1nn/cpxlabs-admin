from __future__ import annotations

import unittest

from engineering_graph.planner import PlannedTask, build_execution_plan


def task(
    canonical_id: str,
    *,
    status: str = "pending",
    dependencies: tuple[str, ...] = (),
    artifacts: tuple[str, ...] = (),
    priority: int | None = None,
) -> PlannedTask:
    return PlannedTask(
        canonical_id=canonical_id,
        status=status,
        priority=priority,
        dependencies=frozenset(dependencies),
        artifacts=frozenset(artifacts),
    )


class PlannerTests(unittest.TestCase):
    def test_waves_respect_dependencies_and_shared_artifact_conflicts(self) -> None:
        tasks = [
            task("A", artifacts=("src/auth.ts",), priority=1),
            task("B", artifacts=("src/auth.ts",), priority=2),
            task("C", artifacts=("src/dashboard.ts",), priority=3),
            task("D", dependencies=("A",), artifacts=("tests/auth.e2e.ts",)),
        ]
        plan = build_execution_plan(tasks)

        self.assertEqual(plan.ready, ("A", "B", "C"))
        self.assertIn(("A", "C"), plan.waves)
        self.assertIn(("B", "D"), plan.waves)
        self.assertEqual(len(plan.conflicts), 1)
        self.assertEqual(plan.conflicts[0].left, "A")
        self.assertEqual(plan.conflicts[0].right, "B")
        self.assertEqual(plan.conflicts[0].artifacts, ("src/auth.ts",))

    def test_done_dependencies_are_satisfied(self) -> None:
        plan = build_execution_plan(
            [
                task("A", status="done"),
                task("B", dependencies=("A",)),
            ]
        )
        self.assertEqual(plan.ready, ("B",))
        self.assertEqual(plan.waves, (("B",),))

    def test_cycle_is_reported_and_waves_are_not_generated(self) -> None:
        plan = build_execution_plan(
            [
                task("A", dependencies=("B",)),
                task("B", dependencies=("C",)),
                task("C", dependencies=("A",)),
            ]
        )
        self.assertEqual(plan.waves, ())
        self.assertEqual(len(plan.cycles), 1)
        self.assertEqual(set(plan.cycles[0][:-1]), {"A", "B", "C"})

    def test_unknown_dependency_keeps_task_blocked(self) -> None:
        plan = build_execution_plan([task("A", dependencies=("EXTERNAL",))])
        self.assertEqual(plan.ready, ())
        self.assertEqual(plan.blocked, (("A", ("EXTERNAL",)),))
        self.assertEqual(plan.waves, ())


if __name__ == "__main__":
    unittest.main()
