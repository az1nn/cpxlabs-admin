from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .config import GraphSettings
from .planner import PlannedTask, detect_cycles, load_tasks_from_store
from .store import GraphStore


@dataclass(frozen=True, slots=True)
class InvariantResult:
    rule: str
    severity: str
    entity: str
    message: str
    source_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "rule": self.rule,
            "severity": self.severity,
            "entity": self.entity,
            "message": self.message,
        }
        if self.source_path:
            result["sourcePath"] = self.source_path
        return result


def _severity(settings: GraphSettings, rule: str, fallback: str = "warning") -> str:
    value = settings.validation_rules.get(rule, fallback).lower()
    if value not in {"error", "warning", "off"}:
        raise ValueError(f"Invalid validation severity for {rule}: {value}")
    return value


def _is_historical(settings: GraphSettings, spec_id: str | None) -> bool:
    if not spec_id:
        return False
    return any(spec_id.startswith(prefix) for prefix in settings.historical_spec_prefixes)


def _add_rows(
    results: list[InvariantResult],
    settings: GraphSettings,
    rule: str,
    rows: Iterable[dict[str, Any]],
    message: str,
    *,
    fallback: str = "warning",
    historical_downgrade: bool = False,
) -> None:
    configured = _severity(settings, rule, fallback)
    if configured == "off":
        return
    for row in rows:
        severity = configured
        spec_id = str(row.get("specId") or "") or None
        if historical_downgrade and severity == "error" and _is_historical(settings, spec_id):
            severity = "warning"
        results.append(
            InvariantResult(
                rule=rule,
                severity=severity,
                entity=str(row.get("entity") or row.get("canonicalId") or "unknown"),
                message=message.format(**{key: value for key, value in row.items()}),
                source_path=str(row["sourcePath"]) if row.get("sourcePath") else None,
            )
        )


def validate_graph(store: GraphStore, settings: GraphSettings) -> list[InvariantResult]:
    repository = settings.repository_id
    results: list[InvariantResult] = []

    _add_rows(
        results,
        settings,
        "enforced-spec-no-task",
        store.run(
            """
            MATCH (s:Spec {repository: $repository})
            WHERE coalesce(s.enforced, false) = true
              AND NOT EXISTS { MATCH (s)-[:DECOMPOSED_INTO]->(:Task) }
            RETURN s.canonicalId AS entity, s.canonicalId AS specId, s.sourcePath AS sourcePath
            ORDER BY entity
            """,
            {"repository": repository},
        ),
        "Enforced spec {entity} has no decomposed tasks",
        fallback="error",
    )

    completed_without_code = store.run(
        """
        MATCH (t:Task {repository: $repository, status: 'done'})
        WHERE NOT EXISTS { MATCH (t)-[:IMPLEMENTED_BY]->(:CodeArtifact) }
        RETURN t.canonicalId AS entity, t.specId AS specId, t.sourcePath AS sourcePath
        ORDER BY entity
        """,
        {"repository": repository},
    )
    _add_rows(
        results,
        settings,
        "completed-task-no-code",
        completed_without_code,
        "Completed task {entity} has no explicit implementation artifact",
        historical_downgrade=True,
    )

    completed_without_test = store.run(
        """
        MATCH (t:Task {repository: $repository, status: 'done'})
        WHERE NOT EXISTS { MATCH (t)-[:VALIDATED_BY]->(:Test) }
        RETURN t.canonicalId AS entity, t.specId AS specId, t.sourcePath AS sourcePath
        ORDER BY entity
        """,
        {"repository": repository},
    )
    _add_rows(
        results,
        settings,
        "completed-task-no-test",
        completed_without_test,
        "Completed task {entity} has no explicit validation artifact",
        historical_downgrade=True,
    )

    critical_without_test = store.run(
        """
        MATCH (r:Requirement {repository: $repository, critical: true})-[:REALIZED_BY]->(s:Spec)
        WHERE NOT EXISTS {
          MATCH (s)-[:DECOMPOSED_INTO]->(:Task)-[:VALIDATED_BY]->(:Test)
        }
        RETURN r.canonicalId AS entity, s.canonicalId AS specId, r.sourcePath AS sourcePath
        ORDER BY entity
        """,
        {"repository": repository},
    )
    _add_rows(
        results,
        settings,
        "critical-requirement-no-test",
        critical_without_test,
        "Critical requirement {entity} has no validation evidence through its spec tasks",
        historical_downgrade=True,
    )

    orphan_adrs = store.run(
        """
        MATCH (a:ADR {repository: $repository})
        WHERE NOT EXISTS { MATCH (:Spec)-[:CONSTRAINED_BY]->(a) }
        RETURN a.canonicalId AS entity, a.sourcePath AS sourcePath
        ORDER BY entity
        """,
        {"repository": repository},
    )
    _add_rows(
        results,
        settings,
        "adr-no-consumer",
        orphan_adrs,
        "ADR {entity} has no explicit Spec consumer",
    )

    task_rule = _severity(settings, "task-dependency-cycle", "error")
    if task_rule != "off":
        tasks = load_tasks_from_store(store, repository)
        cycles = detect_cycles({task.canonical_id: task for task in tasks})
        for cycle in cycles:
            results.append(
                InvariantResult(
                    rule="task-dependency-cycle",
                    severity=task_rule,
                    entity=cycle[0],
                    message="Task dependency cycle: " + " -> ".join(cycle),
                )
            )

    return sorted(results, key=lambda item: (item.severity != "error", item.rule, item.entity))


def has_errors(results: Iterable[InvariantResult]) -> bool:
    return any(result.severity == "error" for result in results)
