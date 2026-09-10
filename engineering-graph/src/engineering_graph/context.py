from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .config import ContextBudget, GraphSettings
from .store import GraphStore


@dataclass(frozen=True, slots=True)
class ContextPackage:
    task: dict[str, Any]
    spec: dict[str, Any] | None
    requirements: tuple[dict[str, Any], ...]
    adrs: tuple[dict[str, Any], ...]
    dependencies: tuple[dict[str, Any], ...]
    code: tuple[dict[str, Any], ...]
    tests: tuple[dict[str, Any], ...]
    pull_requests: tuple[dict[str, Any], ...]
    budget: ContextBudget
    truncated: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "spec": self.spec,
            "requirements": list(self.requirements),
            "adrs": list(self.adrs),
            "dependencies": list(self.dependencies),
            "code": list(self.code),
            "tests": list(self.tests),
            "pullRequests": list(self.pull_requests),
            "budget": {
                "maxDepth": self.budget.max_depth,
                "maxNodes": self.budget.max_nodes,
            },
            "truncated": self.truncated,
        }


def _clean(values: list[Any] | None) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for value in values or []:
        if not isinstance(value, dict):
            continue
        canonical = str(value.get("canonicalId") or value.get("path") or repr(value))
        unique[canonical] = value
    return [unique[key] for key in sorted(unique)]


def _take(
    values: list[dict[str, Any]],
    remaining: int,
) -> tuple[tuple[dict[str, Any], ...], int, bool]:
    if remaining <= 0:
        return (), 0, bool(values)
    selected = values[:remaining]
    return tuple(selected), remaining - len(selected), len(selected) < len(values)


def build_context(
    store: GraphStore,
    settings: GraphSettings,
    task_id: str,
    budget: ContextBudget | None = None,
) -> ContextPackage:
    effective = budget or settings.context
    rows = store.query_file(
        "agent-context.cypher",
        {"repository": settings.repository_id, "taskId": task_id},
    )
    if not rows:
        raise LookupError(f"Task not found in engineering graph: {task_id}")
    row = rows[0]
    task = row.get("task")
    if not isinstance(task, dict):
        raise LookupError(f"Task not found in engineering graph: {task_id}")
    spec = row.get("spec") if isinstance(row.get("spec"), dict) else None

    # Task and parent Spec consume the first slots. Related collections then consume
    # a deterministic shared node budget so context size cannot grow unbounded.
    remaining = max(effective.max_nodes - 1 - (1 if spec else 0), 0)
    truncated = False
    groups: list[tuple[str, list[dict[str, Any]]]] = [
        ("requirements", _clean(row.get("requirements"))),
        ("adrs", _clean(row.get("adrs"))),
        ("dependencies", _clean(row.get("dependencies"))),
        ("code", _clean(row.get("code"))),
        ("tests", _clean(row.get("tests"))),
        ("pullRequests", _clean(row.get("pullRequests"))),
    ]
    selected: dict[str, tuple[dict[str, Any], ...]] = {}
    for name, values in groups:
        chunk, remaining, group_truncated = _take(values, remaining)
        selected[name] = chunk
        truncated = truncated or group_truncated

    return ContextPackage(
        task=task,
        spec=spec,
        requirements=selected["requirements"],
        adrs=selected["adrs"],
        dependencies=selected["dependencies"],
        code=selected["code"],
        tests=selected["tests"],
        pull_requests=selected["pullRequests"],
        budget=effective,
        truncated=truncated,
    )


def render_context_markdown(package: ContextPackage) -> str:
    def entity_line(value: dict[str, Any], fallback: str = "unknown") -> str:
        identity = value.get("canonicalId") or value.get("path") or fallback
        title = value.get("title") or value.get("text")
        source = value.get("sourcePath") or value.get("path")
        suffix = f" — {title}" if title else ""
        location = f" (`{source}`)" if source else ""
        return f"- **{identity}**{suffix}{location}"

    lines = [
        f"# Agent Context: {package.task.get('canonicalId', 'Task')}",
        "",
        f"Budget: depth ≤ {package.budget.max_depth}, nodes ≤ {package.budget.max_nodes}",
        f"Truncated: {'yes' if package.truncated else 'no'}",
        "",
        "## Task",
        entity_line(package.task),
    ]
    sections = [
        ("Parent Spec", [package.spec] if package.spec else []),
        ("Requirements", package.requirements),
        ("Architecture Decisions", package.adrs),
        ("Dependencies", package.dependencies),
        ("Likely Code", package.code),
        ("Tests", package.tests),
        ("Pull Request Evidence", package.pull_requests),
    ]
    for title, values in sections:
        lines.extend(["", f"## {title}"])
        if values:
            lines.extend(entity_line(value) for value in values if value is not None)
        else:
            lines.append("- None linked")
    lines.extend(
        [
            "",
            "## Source-of-truth rule",
            "This package is derived navigation context. Read and edit the canonical repository files referenced above; do not treat Neo4j as authoritative content.",
            "",
        ]
    )
    return "\n".join(lines)


def write_context(package: ContextPackage, format_name: str, output: Path | None = None) -> str:
    if format_name == "json":
        rendered = json.dumps(package.to_dict(), indent=2, sort_keys=True, default=str)
    elif format_name == "markdown":
        rendered = render_context_markdown(package)
    else:
        raise ValueError(f"Unsupported context format: {format_name}")
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + ("\n" if not rendered.endswith("\n") else ""), encoding="utf-8")
    return rendered
