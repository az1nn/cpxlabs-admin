from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .agent_adapters import validation_commands, write_agent_handoff
from .config import GraphSettings
from .context import ContextPackage, build_context, write_context
from .context_validation import inspect_freshness
from .execution import (
    ExecutionAllocation,
    ExecutionManifest,
    build_execution_manifest,
    planned_allocation,
    validate_execution_manifest,
)
from .leases import (
    LeaseRegistryError,
    acquire_lease,
    active_lease,
    assert_allocation_available,
    load_registry,
    release_lease,
)
from .planner import build_execution_plan, load_tasks_from_store
from .store import GraphStore
from .worktrees import (
    GitWorktreeError,
    branch_name_for_task,
    current_revision,
    ensure_worktree,
    is_worktree_dirty,
    list_worktrees,
    normalize_task_component,
    remove_worktree,
    worktree_path_for_task,
)


@dataclass(frozen=True, slots=True)
class PreparationResult:
    repository: str
    source_revision: str
    spec_id: str | None
    allocations: tuple[ExecutionAllocation, ...]
    dry_run: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "sourceRevision": self.source_revision,
            "specId": self.spec_id,
            "dryRun": self.dry_run,
            "allocationCount": len(self.allocations),
            "allocations": [allocation.to_dict() for allocation in self.allocations],
        }


def execution_root(settings: GraphSettings, override: Path | None = None) -> Path:
    return (override or settings.tool_root / ".execution").resolve()


def _task_spec_id(task_id: str, manifest_spec: str | None) -> str:
    if manifest_spec:
        return manifest_spec
    if ":T" in task_id:
        return task_id.rsplit(":T", 1)[0]
    return "unscoped"


def _context_paths(root: Path, task_id: str, agent: str) -> tuple[Path, Path, Path]:
    directory = root / "contexts" / normalize_task_component(task_id)
    return directory / "context.json", directory / "context.md", directory / f"{agent}.md"


def _projection_revisions(
    store: GraphStore,
    repository: str,
    spec_id: str | None,
) -> tuple[str, ...]:
    rows = store.run(
        """
        MATCH (task:Task {repository: $repository})
        WHERE $specId IS NULL OR task.specId = $specId
        RETURN collect(DISTINCT task.sourceRevision) AS revisions
        """,
        {"repository": repository, "specId": spec_id},
    )
    values = rows[0].get("revisions") if rows else []
    return tuple(sorted(str(value) for value in (values or []) if value))


def build_manifest_from_store(
    store: GraphStore,
    settings: GraphSettings,
    *,
    spec_id: str | None,
    agent: str,
) -> ExecutionManifest:
    revision = current_revision(settings.repo_root)
    projected_revisions = _projection_revisions(store, settings.repository_id, spec_id)
    if len(projected_revisions) > 1:
        raise RuntimeError(
            "Selected task graph contains multiple source revisions; run a full graph sync before planning"
        )
    if projected_revisions and projected_revisions[0] != revision:
        raise RuntimeError(
            f"Engineering Graph projection is stale: graph={projected_revisions[0]} HEAD={revision}"
        )

    tasks = load_tasks_from_store(store, settings.repository_id, spec_id)
    plan = build_execution_plan(tasks)
    return build_execution_manifest(
        plan,
        repository=settings.repository_id,
        source_revision=revision,
        spec_id=spec_id,
        agent=agent,
    )


def select_manifest_tasks(
    manifest: ExecutionManifest,
    *,
    wave: int | None = None,
    task_ids: Iterable[str] = (),
) -> tuple[str, ...]:
    validate_execution_manifest(manifest)
    if manifest.cycles:
        rendered = "; ".join(" -> ".join(cycle) for cycle in manifest.cycles)
        raise ValueError(f"Execution manifest contains task dependency cycles: {rendered}")

    explicit = tuple(sorted({task.strip() for task in task_ids if task.strip()}))
    if wave is not None and explicit:
        raise ValueError("Select either --wave or explicit --task values, not both")
    if wave is None and not explicit:
        raise ValueError("Execution preparation requires --wave or at least one --task")

    if wave is not None:
        if wave < 1:
            raise ValueError("Execution wave index must be positive")
        selected = next((item.tasks for item in manifest.waves if item.index == wave), None)
        if selected is None:
            raise ValueError(f"Execution wave {wave} does not exist in the manifest")
        return selected

    containing = [item for item in manifest.waves if set(explicit) <= set(item.tasks)]
    if len(containing) != 1:
        raise ValueError(
            "Explicit tasks must all belong to one execution wave; selection cannot bypass dependency/conflict safety"
        )
    return explicit


def _assert_manifest_revision(settings: GraphSettings, manifest: ExecutionManifest) -> None:
    current = current_revision(settings.repo_root)
    if current != manifest.source_revision:
        raise RuntimeError(
            f"Execution manifest is stale: manifest={manifest.source_revision} HEAD={current}; replan before preparing"
        )
    if manifest.repository != settings.repository_id:
        raise RuntimeError(
            f"Execution manifest repository mismatch: manifest={manifest.repository!r} expected={settings.repository_id!r}"
        )


def _build_current_packages(
    store: GraphStore,
    settings: GraphSettings,
    manifest: ExecutionManifest,
    selected: tuple[str, ...],
) -> dict[str, ContextPackage]:
    packages: dict[str, ContextPackage] = {}
    for task_id in selected:
        package = build_context(store, settings, task_id)
        report = inspect_freshness(
            package,
            settings.repo_root,
            expected_repository=settings.repository_id,
            strict=True,
        )
        if not report.valid:
            raise RuntimeError(
                f"Context package for {task_id} is not strictly current: {report.status}"
            )
        if package.source_revision != manifest.source_revision:
            raise RuntimeError(
                f"Context/manifest revision mismatch for {task_id}: context={package.source_revision} manifest={manifest.source_revision}"
            )
        packages[task_id] = package
    return packages


def _planned_for_task(
    settings: GraphSettings,
    manifest: ExecutionManifest,
    root: Path,
    task_id: str,
    package: ContextPackage | None,
) -> ExecutionAllocation:
    branch = branch_name_for_task(task_id)
    worktree = worktree_path_for_task(root, task_id)
    context_json, _, handoff = _context_paths(root, task_id, manifest.agent)
    commands = validation_commands(package) if package is not None else ()
    return planned_allocation(
        repository=settings.repository_id,
        task_id=task_id,
        spec_id=_task_spec_id(task_id, manifest.spec_id),
        source_revision=manifest.source_revision,
        agent=manifest.agent,
        branch=branch,
        worktree_path=str(worktree),
        context_path=str(context_json),
        handoff_path=str(handoff),
        validation_commands=commands,
    )


def prepare_execution(
    store: GraphStore,
    settings: GraphSettings,
    manifest: ExecutionManifest,
    *,
    wave: int | None = None,
    task_ids: Iterable[str] = (),
    root_override: Path | None = None,
    dry_run: bool = False,
) -> PreparationResult:
    _assert_manifest_revision(settings, manifest)
    selected = select_manifest_tasks(manifest, wave=wave, task_ids=task_ids)
    root = execution_root(settings, root_override)
    lease_path = root / "leases.json"
    registry = load_registry(lease_path, expected_repository=settings.repository_id)

    packages = _build_current_packages(store, settings, manifest, selected)
    _assert_manifest_revision(settings, manifest)

    planned = tuple(
        _planned_for_task(settings, manifest, root, task_id, packages[task_id])
        for task_id in selected
    )
    for allocation in planned:
        assert_allocation_available(registry, allocation)

    if dry_run:
        return PreparationResult(
            repository=settings.repository_id,
            source_revision=manifest.source_revision,
            spec_id=manifest.spec_id,
            allocations=planned,
            dry_run=True,
        )

    root.mkdir(parents=True, exist_ok=True)
    created_worktrees: list[Path] = []
    acquired_tasks: list[str] = []
    active_allocations: list[ExecutionAllocation] = []
    try:
        for allocation in planned:
            _assert_manifest_revision(settings, manifest)
            package = packages[allocation.task_id]
            context_json = Path(allocation.context_path)
            context_markdown = context_json.with_name("context.md")
            handoff = Path(allocation.handoff_path)
            context_json.parent.mkdir(parents=True, exist_ok=True)
            write_context(package, "json", context_json)
            write_context(package, "markdown", context_markdown)
            write_agent_handoff(package, manifest.agent, handoff, str(context_json))

            _, created = ensure_worktree(
                settings.repo_root,
                path=Path(allocation.worktree_path),
                branch=allocation.branch,
                source_revision=manifest.source_revision,
            )
            if created:
                created_worktrees.append(Path(allocation.worktree_path))

            active = acquire_lease(lease_path, allocation)
            acquired_tasks.append(active.task_id)
            active_allocations.append(active)
    except Exception:
        for task_id in reversed(acquired_tasks):
            try:
                release_lease(lease_path, repository=settings.repository_id, task_id=task_id)
            except LeaseRegistryError:
                pass
        for path in reversed(created_worktrees):
            try:
                remove_worktree(settings.repo_root, path, force=False)
            except GitWorktreeError:
                pass
        raise

    return PreparationResult(
        repository=settings.repository_id,
        source_revision=manifest.source_revision,
        spec_id=manifest.spec_id,
        allocations=tuple(active_allocations),
        dry_run=False,
    )


def execution_status(
    settings: GraphSettings,
    *,
    root_override: Path | None = None,
) -> dict[str, Any]:
    root = execution_root(settings, root_override)
    lease_path = root / "leases.json"
    registry = load_registry(lease_path, expected_repository=settings.repository_id)
    worktrees = list_worktrees(settings.repo_root)
    by_path = {str(item.path.resolve()): item for item in worktrees}

    active: list[dict[str, Any]] = []
    for lease in registry.active:
        payload = lease.to_dict()
        descriptor = by_path.get(str(Path(lease.worktree_path).resolve()))
        payload["worktreeRegistered"] = descriptor is not None
        payload["dirty"] = (
            is_worktree_dirty(Path(lease.worktree_path))
            if descriptor is not None and Path(lease.worktree_path).exists()
            else None
        )
        active.append(payload)
    return {
        "repository": settings.repository_id,
        "executionRoot": str(root),
        "activeCount": len(active),
        "active": active,
    }


def release_execution(
    settings: GraphSettings,
    task_id: str,
    *,
    root_override: Path | None = None,
    remove: bool = False,
    force: bool = False,
) -> ExecutionAllocation:
    root = execution_root(settings, root_override)
    lease_path = root / "leases.json"
    registry = load_registry(lease_path, expected_repository=settings.repository_id)
    lease = active_lease(registry, task_id)
    if lease is None:
        raise LeaseRegistryError(f"No active lease exists for task {task_id}")

    if remove:
        remove_worktree(settings.repo_root, Path(lease.worktree_path), force=force)
    return release_lease(lease_path, repository=settings.repository_id, task_id=task_id)
