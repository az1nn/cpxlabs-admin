from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .model import GraphEdge, GraphModel, GraphNode
from .store import GraphStore


@dataclass(frozen=True, slots=True)
class PlannedTask:
    canonical_id: str
    status: str
    priority: int | None
    dependencies: frozenset[str]
    artifacts: frozenset[str]


@dataclass(frozen=True, slots=True)
class TaskConflict:
    left: str
    right: str
    artifacts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    ready: tuple[str, ...]
    blocked: tuple[tuple[str, tuple[str, ...]], ...]
    cycles: tuple[tuple[str, ...], ...]
    conflicts: tuple[TaskConflict, ...]
    waves: tuple[tuple[str, ...], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": list(self.ready),
            "blocked": [
                {"task": task, "blockedBy": list(blockers)}
                for task, blockers in self.blocked
            ],
            "cycles": [list(cycle) for cycle in self.cycles],
            "conflicts": [
                {
                    "left": conflict.left,
                    "right": conflict.right,
                    "artifacts": list(conflict.artifacts),
                }
                for conflict in self.conflicts
            ],
            "waves": [list(wave) for wave in self.waves],
        }


class TaskDependencyCycleError(RuntimeError):
    def __init__(self, cycles: tuple[tuple[str, ...], ...]) -> None:
        self.cycles = cycles
        rendered = "; ".join(" -> ".join(cycle) for cycle in cycles)
        super().__init__(f"Task dependency cycle detected: {rendered}")


def _task_sort_key(task: PlannedTask) -> tuple[int, str]:
    return (task.priority if task.priority is not None else 1_000_000, task.canonical_id)


def detect_cycles(tasks: dict[str, PlannedTask]) -> tuple[tuple[str, ...], ...]:
    pending_ids = set(tasks)
    adjacency = {
        task_id: sorted(dependency for dependency in task.dependencies if dependency in pending_ids)
        for task_id, task in tasks.items()
    }
    state: dict[str, int] = {}
    stack: list[str] = []
    cycles: set[tuple[str, ...]] = set()

    def canonicalize_cycle(cycle: list[str]) -> tuple[str, ...]:
        body = cycle[:-1]
        if not body:
            return tuple(cycle)
        minimum = min(range(len(body)), key=lambda index: body[index])
        rotated = body[minimum:] + body[:minimum]
        return tuple(rotated + [rotated[0]])

    def visit(task_id: str) -> None:
        current = state.get(task_id, 0)
        if current == 2:
            return
        if current == 1:
            if task_id in stack:
                start = stack.index(task_id)
                cycles.add(canonicalize_cycle(stack[start:] + [task_id]))
            return
        state[task_id] = 1
        stack.append(task_id)
        for dependency in adjacency.get(task_id, []):
            visit(dependency)
        stack.pop()
        state[task_id] = 2

    for task_id in sorted(tasks):
        visit(task_id)
    return tuple(sorted(cycles))


def find_conflicts(tasks: Iterable[PlannedTask]) -> tuple[TaskConflict, ...]:
    pending = sorted((task for task in tasks if task.status == "pending"), key=_task_sort_key)
    result: list[TaskConflict] = []
    for index, left in enumerate(pending):
        for right in pending[index + 1 :]:
            overlap = tuple(sorted(left.artifacts & right.artifacts))
            if overlap:
                result.append(TaskConflict(left.canonical_id, right.canonical_id, overlap))
    return tuple(result)


def build_execution_plan(tasks: Iterable[PlannedTask]) -> ExecutionPlan:
    all_tasks = {task.canonical_id: task for task in tasks}
    pending = {task_id: task for task_id, task in all_tasks.items() if task.status == "pending"}
    cycles = detect_cycles(pending)
    conflicts = find_conflicts(all_tasks.values())

    done = {task_id for task_id, task in all_tasks.items() if task.status == "done"}
    unresolved: dict[str, set[str]] = {}
    for task_id, task in pending.items():
        unresolved[task_id] = {
            dependency for dependency in task.dependencies if dependency not in done
        }

    ready = tuple(
        task_id
        for task_id in sorted(pending, key=lambda item: _task_sort_key(pending[item]))
        if not unresolved[task_id]
    )
    blocked = tuple(
        (task_id, tuple(sorted(unresolved[task_id])))
        for task_id in sorted(pending, key=lambda item: _task_sort_key(pending[item]))
        if unresolved[task_id]
    )

    if cycles:
        return ExecutionPlan(ready, blocked, cycles, conflicts, ())

    remaining = set(pending)
    completed = set(done)
    waves: list[tuple[str, ...]] = []

    while remaining:
        candidates = [
            pending[task_id]
            for task_id in remaining
            if pending[task_id].dependencies <= completed
        ]
        candidates.sort(key=_task_sort_key)
        if not candidates:
            # Dependencies may reference a task outside the selected graph/spec.
            break

        wave: list[PlannedTask] = []
        occupied_artifacts: set[str] = set()
        for task in candidates:
            if task.artifacts & occupied_artifacts:
                continue
            wave.append(task)
            occupied_artifacts.update(task.artifacts)

        if not wave:
            break
        wave_ids = tuple(task.canonical_id for task in wave)
        waves.append(wave_ids)
        remaining.difference_update(wave_ids)
        completed.update(wave_ids)

    return ExecutionPlan(ready, blocked, (), conflicts, tuple(waves))


def assert_no_task_cycles(model: GraphModel) -> None:
    tasks: dict[str, PlannedTask] = {}
    for node in model.nodes_by_label("Task"):
        dependencies = frozenset(
            edge.target_id
            for edge in model.edges_from("Task", node.canonical_id, "DEPENDS_ON")
            if edge.target_label == "Task"
        )
        tasks[node.canonical_id] = PlannedTask(
            canonical_id=node.canonical_id,
            status=str(node.properties.get("status", "pending")),
            priority=node.properties.get("priority") if isinstance(node.properties.get("priority"), int) else None,
            dependencies=dependencies,
            artifacts=frozenset(
                edge.target_id
                for edge in model.edges_from("Task", node.canonical_id)
                if edge.relationship in {"IMPLEMENTED_BY", "VALIDATED_BY"}
            ),
        )
    cycles = detect_cycles(tasks)
    if cycles:
        raise TaskDependencyCycleError(cycles)


def load_tasks_from_store(
    store: GraphStore,
    repository: str,
    spec_id: str | None = None,
) -> list[PlannedTask]:
    rows = store.run(
        """
        MATCH (t:Task {repository: $repository})
        WHERE $specId IS NULL OR t.specId = $specId
        OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dependency:Task {repository: $repository})
        WITH t, collect(DISTINCT dependency.canonicalId) AS dependencies
        OPTIONAL MATCH (t)-[:IMPLEMENTED_BY|VALIDATED_BY]->(artifact)
        RETURN t.canonicalId AS canonicalId,
               t.status AS status,
               t.priority AS priority,
               dependencies,
               collect(DISTINCT artifact.path) AS artifacts
        ORDER BY canonicalId
        """,
        {"repository": repository, "specId": spec_id},
    )
    return [
        PlannedTask(
            canonical_id=str(row["canonicalId"]),
            status=str(row.get("status") or "pending"),
            priority=row.get("priority") if isinstance(row.get("priority"), int) else None,
            dependencies=frozenset(str(value) for value in (row.get("dependencies") or []) if value),
            artifacts=frozenset(str(value) for value in (row.get("artifacts") or []) if value),
        )
        for row in rows
    ]
