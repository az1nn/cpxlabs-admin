from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
from typing import Any

from .config import GraphSettings
from .git import current_revision, ingest_github_event, ingest_merged_pull_requests
from .model import ExtractionIssue, GraphEdge, GraphModel, GraphNode
from .parser import (
    canonical_adr_id,
    canonical_requirement_id,
    canonical_spec_id,
    canonical_task_id,
    code_kind,
    extract_adr_refs,
    extract_spec_refs,
    extract_status,
    extract_title,
    frontmatter_list,
    graph_metadata,
    is_test_path,
    normalize_path,
    parse_frontmatter,
    parse_requirements,
    parse_tasks,
    test_kind,
)


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    model: GraphModel
    source_revision: str


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _relative(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _ensure_path_node(model: GraphModel, repo_root: Path, path: str) -> tuple[str, str]:
    normalized = normalize_path(path)
    exists = (repo_root / normalized).exists()
    if is_test_path(normalized):
        model.add_node(
            GraphNode(
                "Test",
                normalized,
                {"path": normalized, "kind": test_kind(normalized), "exists": exists},
            )
        )
        return "Test", normalized
    model.add_node(
        GraphNode(
            "CodeArtifact",
            normalized,
            {"path": normalized, "kind": code_kind(normalized), "exists": exists},
        )
    )
    return "CodeArtifact", normalized


def _discover_adrs(settings: GraphSettings, model: GraphModel) -> None:
    for path in sorted(settings.repo_root.glob(settings.adr_glob)):
        text = _read(path)
        parsed = parse_frontmatter(text)
        metadata = graph_metadata(parsed.metadata)
        canonical_id = str(metadata.get("id") or canonical_adr_id(path.name)).upper()
        relative = _relative(settings.repo_root, path)
        model.add_node(
            GraphNode(
                "ADR",
                canonical_id,
                {
                    "number": canonical_id.removeprefix("ADR-"),
                    "title": extract_title(parsed.body, path.stem),
                    "status": extract_status(parsed.body, parsed.metadata, "accepted"),
                    "sourcePath": relative,
                },
            )
        )


def _spec_enforced(settings: GraphSettings, spec_id: str, metadata: dict[str, Any]) -> bool:
    if "enforced" in metadata:
        return bool(metadata["enforced"])
    return not any(spec_id.startswith(prefix) for prefix in settings.historical_spec_prefixes)


def _add_spec_edges(
    settings: GraphSettings,
    model: GraphModel,
    spec_id: str,
    source_path: str,
    texts: list[str],
    metadata: dict[str, Any],
) -> None:
    adr_refs = set(frontmatter_list(metadata, "constrained_by"))
    spec_refs = set(frontmatter_list(metadata, "depends_on"))
    for text in texts:
        adr_refs.update(extract_adr_refs(text))
        spec_refs.update(extract_spec_refs(text))

    for adr_id in sorted(str(value).upper() for value in adr_refs):
        model.add_edge(
            GraphEdge(
                "Spec",
                spec_id,
                "CONSTRAINED_BY",
                "ADR",
                adr_id,
                {"sourcePath": source_path, "provenance": "explicit"},
            )
        )

    for dependency in sorted(str(value).upper() for value in spec_refs):
        if dependency == spec_id:
            continue
        model.add_edge(
            GraphEdge(
                "Spec",
                spec_id,
                "DEPENDS_ON",
                "Spec",
                dependency,
                {"sourcePath": source_path, "provenance": "explicit"},
            )
        )


def _task_link_metadata(metadata: dict[str, Any], source_id: str) -> dict[str, Any]:
    links = metadata.get("task_links", {})
    if not isinstance(links, dict):
        return {}
    value = links.get(source_id) or links.get(source_id.upper())
    return value if isinstance(value, dict) else {}


def _discover_specs(settings: GraphSettings, model: GraphModel) -> None:
    for spec_path in sorted(settings.repo_root.glob(settings.specs_glob)):
        feature_dir = spec_path.parent.name
        text = _read(spec_path)
        parsed = parse_frontmatter(text)
        metadata = graph_metadata(parsed.metadata)
        default_spec_id = canonical_spec_id(feature_dir)
        spec_id = str(metadata.get("id") or default_spec_id).upper()
        source_path = _relative(settings.repo_root, spec_path)
        feature_number, slug = feature_dir.split("-", 1)

        model.add_node(
            GraphNode(
                "Spec",
                spec_id,
                {
                    "featureId": feature_number,
                    "slug": slug,
                    "title": extract_title(parsed.body, feature_dir),
                    "status": extract_status(parsed.body, parsed.metadata, "active"),
                    "sourcePath": source_path,
                    "enforced": _spec_enforced(settings, spec_id, metadata),
                },
            )
        )

        for requirement in parse_requirements(parsed.body, parsed.body_start_line):
            requirement_id = canonical_requirement_id(spec_id, requirement.source_id)
            model.add_node(
                GraphNode(
                    "Requirement",
                    requirement_id,
                    {
                        "sourceId": requirement.source_id,
                        "kind": requirement.kind,
                        "text": requirement.text,
                        "critical": requirement.critical,
                        "sourcePath": source_path,
                        "line": requirement.line,
                    },
                )
            )
            model.add_edge(
                GraphEdge(
                    "Requirement",
                    requirement_id,
                    "REALIZED_BY",
                    "Spec",
                    spec_id,
                    {"sourcePath": source_path, "provenance": "convention"},
                )
            )

        supporting_texts = [parsed.body]
        plan_path = spec_path.parent / settings.plans_name
        if plan_path.exists():
            supporting_texts.append(parse_frontmatter(_read(plan_path)).body)
        _add_spec_edges(settings, model, spec_id, source_path, supporting_texts, metadata)

        tasks_path = spec_path.parent / settings.tasks_name
        if not tasks_path.exists():
            continue
        tasks_text = _read(tasks_path)
        tasks_parsed = parse_frontmatter(tasks_text)
        tasks_metadata = graph_metadata(tasks_parsed.metadata)
        task_source_path = _relative(settings.repo_root, tasks_path)
        parsed_tasks = parse_tasks(tasks_parsed.body, tasks_parsed.body_start_line)

        for task in parsed_tasks:
            task_id = canonical_task_id(spec_id, task.source_id)
            model.add_node(
                GraphNode(
                    "Task",
                    task_id,
                    {
                        "sourceId": task.source_id,
                        "title": task.title,
                        "status": task.status,
                        "priority": None,
                        "parallel": task.parallel,
                        "userStory": task.user_story,
                        "phase": task.phase,
                        "sourcePath": task_source_path,
                        "line": task.line,
                        "specId": spec_id,
                    },
                )
            )
            model.add_edge(
                GraphEdge(
                    "Spec",
                    spec_id,
                    "DECOMPOSED_INTO",
                    "Task",
                    task_id,
                    {"sourcePath": task_source_path, "provenance": "convention"},
                )
            )

        for task in parsed_tasks:
            task_id = canonical_task_id(spec_id, task.source_id)
            for dependency in task.dependencies:
                model.add_edge(
                    GraphEdge(
                        "Task",
                        task_id,
                        "DEPENDS_ON",
                        "Task",
                        canonical_task_id(spec_id, dependency),
                        {"sourcePath": task_source_path, "provenance": "explicit"},
                    )
                )

            task_metadata = _task_link_metadata(tasks_metadata, task.source_id)
            implementation_paths = set(task.paths)
            implementation_paths.update(frontmatter_list(task_metadata, "implements"))
            validation_paths = set(frontmatter_list(task_metadata, "validated_by"))

            for path in sorted(implementation_paths):
                label, path_id = _ensure_path_node(model, settings.repo_root, path)
                relationship = "VALIDATED_BY" if label == "Test" else "IMPLEMENTED_BY"
                model.add_edge(
                    GraphEdge(
                        "Task",
                        task_id,
                        relationship,
                        label,
                        path_id,
                        {"sourcePath": task_source_path, "provenance": "explicit"},
                    )
                )
            for path in sorted(validation_paths):
                normalized = normalize_path(path)
                label, path_id = _ensure_path_node(model, settings.repo_root, normalized)
                if label != "Test":
                    model.add_issue(
                        ExtractionIssue(
                            "validation-path-not-test",
                            f"validated_by path is not classified as a test: {normalized}",
                            task_source_path,
                            task_id,
                        )
                    )
                    continue
                model.add_edge(
                    GraphEdge(
                        "Task",
                        task_id,
                        "VALIDATED_BY",
                        "Test",
                        path_id,
                        {"sourcePath": task_source_path, "provenance": "explicit"},
                    )
                )


def extract_repository(
    settings: GraphSettings,
    github_event_path: Path | None = None,
) -> ExtractionResult:
    model = GraphModel()
    revision = current_revision(settings.repo_root)
    _discover_adrs(settings, model)
    _discover_specs(settings, model)
    ingest_merged_pull_requests(model, settings.repo_root, settings.repository_id)
    event = github_event_path
    if event is None and os.getenv("GITHUB_EVENT_PATH"):
        event = Path(os.environ["GITHUB_EVENT_PATH"])
    ingest_github_event(model, settings.repo_root, settings.repository_id, event)
    return ExtractionResult(model=model, source_revision=revision)
