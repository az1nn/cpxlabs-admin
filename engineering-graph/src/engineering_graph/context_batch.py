from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
from typing import Any, Iterable

from .agent_adapters import write_agent_handoff
from .config import ContextBudget, GraphSettings
from .context import ContextPackage, build_context, write_context
from .store import GraphStore

MANIFEST_VERSION = "1"


@dataclass(frozen=True, slots=True)
class GeneratedPackage:
    task_id: str
    directory: str
    context_json: str
    context_markdown: str
    codex_handoff: str
    claude_handoff: str
    included_nodes: int
    truncated_nodes: int
    rendered_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "taskId": self.task_id,
            "directory": self.directory,
            "contextJson": self.context_json,
            "contextMarkdown": self.context_markdown,
            "codexHandoff": self.codex_handoff,
            "claudeHandoff": self.claude_handoff,
            "includedNodes": self.included_nodes,
            "truncatedNodes": self.truncated_nodes,
            "renderedBytes": self.rendered_bytes,
        }


@dataclass(frozen=True, slots=True)
class PackageManifest:
    repository: str
    source_revision: str
    spec_id: str | None
    packages: tuple[GeneratedPackage, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifestVersion": MANIFEST_VERSION,
            "repository": self.repository,
            "sourceRevision": self.source_revision,
            "specId": self.spec_id,
            "packageCount": len(self.packages),
            "tasks": [package.to_dict() for package in self.packages],
        }


def ready_task_ids(store: GraphStore, settings: GraphSettings, spec_id: str) -> tuple[str, ...]:
    rows = store.query_file(
        "ready-tasks.cypher",
        {"repository": settings.repository_id, "specId": spec_id},
    )
    task_ids = {
        str(row.get("task"))
        for row in rows
        if row.get("ready") is True and row.get("task")
    }
    return tuple(sorted(task_ids))


def select_task_ids(
    store: GraphStore,
    settings: GraphSettings,
    *,
    spec_id: str | None,
    explicit_task_ids: Iterable[str] = (),
) -> tuple[str, ...]:
    explicit = tuple(sorted({task.strip() for task in explicit_task_ids if task.strip()}))
    if explicit:
        return explicit
    if not spec_id:
        raise ValueError("context-batch requires --spec or at least one --task")
    return ready_task_ids(store, settings, spec_id)


def _safe_component(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return normalized or "context"


def _spec_id_for_task(task_id: str) -> str:
    if ":T" in task_id:
        return task_id.rsplit(":T", 1)[0]
    return "unscoped"


def _write_package_directory(
    package: ContextPackage,
    output_root: Path,
) -> GeneratedPackage:
    task_id = str(package.task.get("canonicalId") or "unknown")
    spec_id = _spec_id_for_task(task_id)
    directory = output_root / _safe_component(spec_id) / _safe_component(task_id)
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)

    context_json = directory / "context.json"
    context_markdown = directory / "context.md"
    codex_handoff = directory / "codex.md"
    claude_handoff = directory / "claude.md"

    write_context(package, "json", context_json)
    write_context(package, "markdown", context_markdown)
    write_agent_handoff(package, "codex", codex_handoff, "context.json")
    write_agent_handoff(package, "claude", claude_handoff, "context.json")

    def relative(path: Path) -> str:
        return path.relative_to(output_root).as_posix()

    return GeneratedPackage(
        task_id=task_id,
        directory=relative(directory),
        context_json=relative(context_json),
        context_markdown=relative(context_markdown),
        codex_handoff=relative(codex_handoff),
        claude_handoff=relative(claude_handoff),
        included_nodes=package.summary.included_nodes,
        truncated_nodes=package.summary.truncated_nodes,
        rendered_bytes=package.summary.rendered_bytes,
    )


def generate_context_packages(
    store: GraphStore,
    settings: GraphSettings,
    *,
    spec_id: str | None = None,
    explicit_task_ids: Iterable[str] = (),
    output_root: Path | None = None,
    budget: ContextBudget | None = None,
) -> PackageManifest:
    destination = (output_root or settings.tool_root / "context-packages").resolve()
    destination.mkdir(parents=True, exist_ok=True)
    selected = select_task_ids(
        store,
        settings,
        spec_id=spec_id,
        explicit_task_ids=explicit_task_ids,
    )
    if not selected:
        raise LookupError("No tasks selected for context package generation")

    generated: list[GeneratedPackage] = []
    source_revision: str | None = None
    for task_id in selected:
        package = build_context(store, settings, task_id, budget)
        if source_revision is None:
            source_revision = package.source_revision
        elif package.source_revision != source_revision:
            raise RuntimeError("Repository revision changed during context package generation")
        generated.append(_write_package_directory(package, destination))

    manifest = PackageManifest(
        repository=settings.repository_id,
        source_revision=source_revision or "unknown",
        spec_id=spec_id,
        packages=tuple(generated),
    )
    manifest_path = destination / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
