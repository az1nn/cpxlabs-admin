from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import GraphSettings
from .extract import ExtractionResult, extract_repository
from .model import GraphModel
from .planner import TaskDependencyCycleError, assert_no_task_cycles
from .store import GraphStore


class SyncValidationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SyncResult:
    repository: str
    source_revision: str
    sync_run_id: str
    node_counts: dict[str, int]
    relationship_counts: dict[str, int]
    extraction_warnings: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "sourceRevision": self.source_revision,
            "syncRunId": self.sync_run_id,
            "nodes": self.node_counts,
            "relationships": self.relationship_counts,
            "extractionWarnings": list(self.extraction_warnings),
        }


def _model_counts(model: GraphModel) -> tuple[dict[str, int], dict[str, int]]:
    node_counts: dict[str, int] = {}
    for node in model.nodes.values():
        node_counts[node.label] = node_counts.get(node.label, 0) + 1
    relationship_counts: dict[str, int] = {}
    for edge in model.edges.values():
        relationship_counts[edge.relationship] = relationship_counts.get(edge.relationship, 0) + 1
    return dict(sorted(node_counts.items())), dict(sorted(relationship_counts.items()))


def validate_extraction(result: ExtractionResult) -> tuple[dict[str, Any], ...]:
    dangling = result.model.dangling_edges()
    if dangling:
        details = ", ".join(
            f"{edge.source_label}:{edge.source_id}-[{edge.relationship}]->"
            f"{edge.target_label}:{edge.target_id}"
            for edge in dangling[:20]
        )
        suffix = " ..." if len(dangling) > 20 else ""
        raise SyncValidationError(f"Dangling explicit graph references: {details}{suffix}")

    try:
        assert_no_task_cycles(result.model)
    except TaskDependencyCycleError as error:
        raise SyncValidationError(str(error)) from error

    warnings = tuple(
        {
            "code": issue.code,
            "message": issue.message,
            **({"sourcePath": issue.source_path} if issue.source_path else {}),
            **({"entityId": issue.entity_id} if issue.entity_id else {}),
        }
        for issue in result.model.issues
    )
    return warnings


def synchronize(
    settings: GraphSettings,
    *,
    repo_root: Path | None = None,
    github_event_path: Path | None = None,
    store: GraphStore | None = None,
) -> SyncResult:
    if repo_root is not None and repo_root.resolve() != settings.repo_root.resolve():
        from .config import load_settings

        settings = load_settings(repo_root=repo_root)

    extraction = extract_repository(settings, github_event_path=github_event_path)
    warnings = validate_extraction(extraction)
    node_counts, relationship_counts = _model_counts(extraction.model)
    sync_run_id = uuid4().hex

    owns_store = store is None
    graph_store = store or GraphStore(settings)
    try:
        graph_store.initialize_schema()
        graph_store.upsert_nodes(
            extraction.model.nodes.values(),
            settings.repository_id,
            extraction.source_revision,
            sync_run_id,
        )
        graph_store.upsert_edges(
            extraction.model.edges.values(),
            settings.repository_id,
            extraction.source_revision,
            sync_run_id,
        )
        if settings.prune_stale:
            graph_store.prune_stale(settings.repository_id, sync_run_id)
    finally:
        if owns_store:
            graph_store.close()

    return SyncResult(
        repository=settings.repository_id,
        source_revision=extraction.source_revision,
        sync_run_id=sync_run_id,
        node_counts=node_counts,
        relationship_counts=relationship_counts,
        extraction_warnings=warnings,
    )
