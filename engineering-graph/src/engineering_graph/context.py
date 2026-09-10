from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .config import ContextBudget, GraphSettings, current_git_revision
from .store import GraphStore

PACKAGE_VERSION = "1"


@dataclass(frozen=True, slots=True)
class ContextProvenance:
    entity_id: str
    relation: str
    via: str | None = None
    source_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"entityId": self.entity_id, "relation": self.relation}
        if self.via:
            payload["via"] = self.via
        if self.source_path:
            payload["sourcePath"] = self.source_path
        return payload


@dataclass(frozen=True, slots=True)
class ContextPackageSummary:
    included_nodes: int
    truncated_nodes: int
    rendered_bytes: int
    truncated: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "includedNodes": self.included_nodes,
            "truncatedNodes": self.truncated_nodes,
            "renderedBytes": self.rendered_bytes,
            "truncated": self.truncated,
        }


@dataclass(frozen=True, slots=True)
class ContextPackage:
    repository: str
    source_revision: str
    task: dict[str, Any]
    spec: dict[str, Any] | None
    requirements: tuple[dict[str, Any], ...]
    adrs: tuple[dict[str, Any], ...]
    dependencies: tuple[dict[str, Any], ...]
    code_artifacts: tuple[dict[str, Any], ...]
    tests: tuple[dict[str, Any], ...]
    pull_requests: tuple[dict[str, Any], ...]
    provenance: tuple[ContextProvenance, ...]
    budget: ContextBudget
    summary: ContextPackageSummary
    generated_at: str
    freshness: str = "current"
    package_version: str = PACKAGE_VERSION

    @property
    def code(self) -> tuple[dict[str, Any], ...]:
        """Compatibility alias for V1 internal callers."""
        return self.code_artifacts

    @property
    def truncated(self) -> bool:
        return self.summary.truncated

    def to_dict(self) -> dict[str, Any]:
        return {
            "packageVersion": self.package_version,
            "repository": self.repository,
            "sourceRevision": self.source_revision,
            "taskId": str(self.task.get("canonicalId") or ""),
            "generatedAt": self.generated_at,
            "freshness": self.freshness,
            "budget": {
                "maxDepth": self.budget.max_depth,
                "maxNodes": self.budget.max_nodes,
                "maxBytes": self.budget.max_bytes,
            },
            "summary": self.summary.to_dict(),
            "task": self.task,
            "spec": self.spec,
            "requirements": list(self.requirements),
            "adrs": list(self.adrs),
            "dependencies": list(self.dependencies),
            "codeArtifacts": list(self.code_artifacts),
            "tests": list(self.tests),
            "pullRequests": list(self.pull_requests),
            "provenance": [entry.to_dict() for entry in self.provenance],
        }

    def semantic_dict(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("generatedAt", None)
        payload.pop("freshness", None)
        summary = dict(payload.get("summary") or {})
        summary.pop("renderedBytes", None)
        payload["summary"] = summary
        return payload

    def semantic_json(self) -> str:
        return json.dumps(self.semantic_dict(), sort_keys=True, separators=(",", ":"), default=str)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ContextPackage":
        required = ("packageVersion", "repository", "sourceRevision", "taskId", "budget", "summary", "task")
        missing = [name for name in required if name not in payload]
        if missing:
            raise ValueError(f"Context package missing required fields: {', '.join(missing)}")
        if payload.get("packageVersion") != PACKAGE_VERSION:
            raise ValueError(f"Unsupported context package version: {payload.get('packageVersion')}")
        task = payload.get("task")
        if not isinstance(task, dict):
            raise ValueError("Context package task must be an object")
        if str(task.get("canonicalId") or "") != str(payload.get("taskId") or ""):
            raise ValueError("Context package taskId does not match task.canonicalId")
        budget_raw = payload.get("budget")
        summary_raw = payload.get("summary")
        if not isinstance(budget_raw, dict) or not isinstance(summary_raw, dict):
            raise ValueError("Context package budget/summary must be objects")

        def dict_tuple(name: str) -> tuple[dict[str, Any], ...]:
            value = payload.get(name, [])
            if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
                raise ValueError(f"Context package {name} must be an array of objects")
            return tuple(value)

        provenance_raw = payload.get("provenance", [])
        if not isinstance(provenance_raw, list):
            raise ValueError("Context package provenance must be an array")
        provenance: list[ContextProvenance] = []
        for value in provenance_raw:
            if not isinstance(value, dict) or not value.get("entityId") or not value.get("relation"):
                raise ValueError("Invalid context package provenance entry")
            provenance.append(
                ContextProvenance(
                    entity_id=str(value["entityId"]),
                    relation=str(value["relation"]),
                    via=str(value["via"]) if value.get("via") is not None else None,
                    source_path=str(value["sourcePath"]) if value.get("sourcePath") is not None else None,
                )
            )

        spec = payload.get("spec")
        if spec is not None and not isinstance(spec, dict):
            raise ValueError("Context package spec must be an object or null")

        return cls(
            package_version=str(payload["packageVersion"]),
            repository=str(payload["repository"]),
            source_revision=str(payload["sourceRevision"]),
            generated_at=str(payload.get("generatedAt") or ""),
            freshness=str(payload.get("freshness") or "unknown"),
            budget=ContextBudget(
                max_depth=int(budget_raw.get("maxDepth", 0)),
                max_nodes=int(budget_raw.get("maxNodes", 0)),
                max_bytes=int(budget_raw.get("maxBytes", 0)),
            ),
            summary=ContextPackageSummary(
                included_nodes=int(summary_raw.get("includedNodes", 0)),
                truncated_nodes=int(summary_raw.get("truncatedNodes", 0)),
                rendered_bytes=int(summary_raw.get("renderedBytes", 0)),
                truncated=bool(summary_raw.get("truncated", False)),
            ),
            task=task,
            spec=spec,
            requirements=dict_tuple("requirements"),
            adrs=dict_tuple("adrs"),
            dependencies=dict_tuple("dependencies"),
            code_artifacts=dict_tuple("codeArtifacts"),
            tests=dict_tuple("tests"),
            pull_requests=dict_tuple("pullRequests"),
            provenance=tuple(provenance),
        )


def _clean(values: list[Any] | None) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for value in values or []:
        if not isinstance(value, dict):
            continue
        canonical = str(value.get("canonicalId") or value.get("path") or repr(value))
        unique[canonical] = value
    return [unique[key] for key in sorted(unique)]


def _entity_id(value: dict[str, Any]) -> str:
    return str(value.get("canonicalId") or value.get("path") or "unknown")


def _source_path(value: dict[str, Any]) -> str | None:
    source = value.get("sourcePath") or value.get("path")
    return str(source) if source else None


def _take(
    values: list[dict[str, Any]],
    remaining: int,
) -> tuple[tuple[dict[str, Any], ...], int]:
    if remaining <= 0:
        return (), 0
    selected = values[:remaining]
    return tuple(selected), remaining - len(selected)


def _provenance(
    task: dict[str, Any],
    spec: dict[str, Any] | None,
    groups: dict[str, tuple[dict[str, Any], ...]],
) -> tuple[ContextProvenance, ...]:
    task_id = _entity_id(task)
    spec_id = _entity_id(spec) if spec else None
    entries: list[ContextProvenance] = []
    if spec:
        entries.append(ContextProvenance(task_id, "DECOMPOSED_INTO", via=spec_id, source_path=_source_path(task)))
    relation_map = {
        "requirements": ("REALIZED_BY", spec_id),
        "adrs": ("CONSTRAINED_BY", spec_id),
        "dependencies": ("DEPENDS_ON", task_id),
        "codeArtifacts": ("IMPLEMENTED_BY", task_id),
        "tests": ("VALIDATED_BY", task_id),
        "pullRequests": ("IMPLEMENTS", task_id),
    }
    for name in ("requirements", "adrs", "dependencies", "codeArtifacts", "tests", "pullRequests"):
        relation, via = relation_map[name]
        for value in groups[name]:
            entries.append(
                ContextProvenance(
                    entity_id=_entity_id(value),
                    relation=relation,
                    via=via,
                    source_path=_source_path(value),
                )
            )
    return tuple(entries)


def _count_nodes(spec: dict[str, Any] | None, groups: dict[str, tuple[dict[str, Any], ...]]) -> int:
    return 1 + (1 if spec else 0) + sum(len(values) for values in groups.values())


def _semantic_bytes(package: ContextPackage) -> int:
    return len(package.semantic_json().encode("utf-8"))


def _with_summary(
    package: ContextPackage,
    total_available_nodes: int,
) -> ContextPackage:
    included = _count_nodes(
        package.spec,
        {
            "requirements": package.requirements,
            "adrs": package.adrs,
            "dependencies": package.dependencies,
            "codeArtifacts": package.code_artifacts,
            "tests": package.tests,
            "pullRequests": package.pull_requests,
        },
    )
    truncated_nodes = max(total_available_nodes - included, 0)
    summary = ContextPackageSummary(
        included_nodes=included,
        truncated_nodes=truncated_nodes,
        rendered_bytes=0,
        truncated=truncated_nodes > 0,
    )
    provisional = replace(package, summary=summary)
    rendered_bytes = _semantic_bytes(provisional)
    return replace(provisional, summary=replace(summary, rendered_bytes=rendered_bytes))


def _enforce_byte_budget(package: ContextPackage, total_available_nodes: int) -> ContextPackage:
    package = _with_summary(package, total_available_nodes)
    if package.summary.rendered_bytes <= package.budget.max_bytes:
        return package

    mutable = {
        "requirements": list(package.requirements),
        "adrs": list(package.adrs),
        "dependencies": list(package.dependencies),
        "codeArtifacts": list(package.code_artifacts),
        "tests": list(package.tests),
        "pullRequests": list(package.pull_requests),
    }
    # Remove lower-priority evidence first. Mandatory Task and parent Spec are retained.
    removal_order = ("pullRequests", "tests", "codeArtifacts", "dependencies", "adrs", "requirements")
    while True:
        changed = False
        for name in removal_order:
            if mutable[name]:
                mutable[name].pop()
                changed = True
                groups = {key: tuple(value) for key, value in mutable.items()}
                candidate = replace(
                    package,
                    requirements=groups["requirements"],
                    adrs=groups["adrs"],
                    dependencies=groups["dependencies"],
                    code_artifacts=groups["codeArtifacts"],
                    tests=groups["tests"],
                    pull_requests=groups["pullRequests"],
                    provenance=_provenance(package.task, package.spec, groups),
                )
                candidate = _with_summary(candidate, total_available_nodes)
                if candidate.summary.rendered_bytes <= candidate.budget.max_bytes:
                    return candidate
                package = candidate
                break
        if not changed:
            raise ValueError(
                "Context max_bytes is too small for mandatory task/spec metadata; increase the byte budget"
            )


def build_context(
    store: GraphStore,
    settings: GraphSettings,
    task_id: str,
    budget: ContextBudget | None = None,
) -> ContextPackage:
    effective = budget or settings.context
    if effective.max_depth < 1 or effective.max_depth > 5:
        raise ValueError("Context max_depth must be between 1 and 5")
    if effective.max_nodes < 1 or effective.max_nodes > 500:
        raise ValueError("Context max_nodes must be between 1 and 500")
    if effective.max_bytes < 1024 or effective.max_bytes > 10_000_000:
        raise ValueError("Context max_bytes must be between 1024 and 10000000")

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

    spec = row.get("spec") if effective.max_depth >= 1 and isinstance(row.get("spec"), dict) else None
    group_depths = {
        "dependencies": 1,
        "codeArtifacts": 1,
        "tests": 1,
        "pullRequests": 1,
        "requirements": 2,
        "adrs": 2,
    }
    raw_groups: dict[str, list[dict[str, Any]]] = {
        "requirements": _clean(row.get("requirements")),
        "adrs": _clean(row.get("adrs")),
        "dependencies": _clean(row.get("dependencies")),
        "codeArtifacts": _clean(row.get("code")),
        "tests": _clean(row.get("tests")),
        "pullRequests": _clean(row.get("pullRequests")),
    }
    total_available_nodes = 1 + (1 if isinstance(row.get("spec"), dict) else 0) + sum(
        len(values) for values in raw_groups.values()
    )

    remaining = max(effective.max_nodes - 1 - (1 if spec else 0), 0)
    selected: dict[str, tuple[dict[str, Any], ...]] = {}
    for name in ("requirements", "adrs", "dependencies", "codeArtifacts", "tests", "pullRequests"):
        values = raw_groups[name]
        if group_depths[name] > effective.max_depth:
            selected[name] = ()
            continue
        chunk, remaining = _take(values, remaining)
        selected[name] = chunk

    source_revision = current_git_revision(settings.repo_root) or "unknown"
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    empty_summary = ContextPackageSummary(0, 0, 0, False)
    package = ContextPackage(
        repository=settings.repository_id,
        source_revision=source_revision,
        generated_at=generated_at,
        freshness="current" if source_revision != "unknown" else "unknown",
        task=task,
        spec=spec,
        requirements=selected["requirements"],
        adrs=selected["adrs"],
        dependencies=selected["dependencies"],
        code_artifacts=selected["codeArtifacts"],
        tests=selected["tests"],
        pull_requests=selected["pullRequests"],
        provenance=_provenance(task, spec, selected),
        budget=effective,
        summary=empty_summary,
    )
    return _enforce_byte_budget(package, total_available_nodes)


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
        f"Repository: `{package.repository}`",
        f"Source revision: `{package.source_revision}`",
        f"Package version: `{package.package_version}`",
        f"Budget: depth ≤ {package.budget.max_depth}, nodes ≤ {package.budget.max_nodes}, bytes ≤ {package.budget.max_bytes}",
        f"Included nodes: {package.summary.included_nodes}; truncated nodes: {package.summary.truncated_nodes}; semantic bytes: {package.summary.rendered_bytes}",
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
        ("Likely Code", package.code_artifacts),
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
            "This package is derived navigation context. Read and edit the canonical repository files referenced above; do not treat Neo4j or generated context files as authoritative content.",
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
