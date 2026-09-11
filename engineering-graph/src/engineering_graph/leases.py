from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .execution import ExecutionAllocation, validate_execution_allocation

REGISTRY_VERSION = "1"


class LeaseRegistryError(RuntimeError):
    pass


class LeaseCollisionError(LeaseRegistryError):
    pass


@dataclass(frozen=True, slots=True)
class LeaseRegistry:
    repository: str
    leases: tuple[ExecutionAllocation, ...]
    registry_version: str = REGISTRY_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "registryVersion": self.registry_version,
            "repository": self.repository,
            "leases": [lease.to_dict() for lease in self.leases],
        }

    @property
    def active(self) -> tuple[ExecutionAllocation, ...]:
        return tuple(lease for lease in self.leases if lease.lease_status == "active")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_registry(path: Path, *, expected_repository: str) -> LeaseRegistry:
    if not path.exists():
        return LeaseRegistry(expected_repository, ())
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise LeaseRegistryError(f"Lease registry is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise LeaseRegistryError("Lease registry root must be a JSON object")
    version = str(raw.get("registryVersion") or "")
    if version != REGISTRY_VERSION:
        raise LeaseRegistryError(f"Unsupported lease registry version: {version}")
    repository = str(raw.get("repository") or "")
    if repository != expected_repository:
        raise LeaseRegistryError(
            f"Lease registry repository mismatch: expected={expected_repository!r} actual={repository!r}"
        )
    raw_leases = raw.get("leases") or []
    if not isinstance(raw_leases, list):
        raise LeaseRegistryError("Lease registry leases must be a JSON array")

    leases: list[ExecutionAllocation] = []
    for raw_lease in raw_leases:
        if not isinstance(raw_lease, dict):
            raise LeaseRegistryError("Lease registry entries must be JSON objects")
        allocation = ExecutionAllocation.from_dict(raw_lease)
        try:
            validate_execution_allocation(allocation)
        except ValueError as error:
            raise LeaseRegistryError(str(error)) from error
        leases.append(allocation)

    registry = LeaseRegistry(repository, tuple(leases), version)
    _validate_active_uniqueness(registry)
    return registry


def _validate_active_uniqueness(registry: LeaseRegistry) -> None:
    tasks: set[str] = set()
    branches: set[str] = set()
    paths: set[str] = set()
    for lease in registry.active:
        resolved_path = str(Path(lease.worktree_path).resolve())
        if lease.task_id in tasks:
            raise LeaseRegistryError(f"Duplicate active lease for task {lease.task_id}")
        if lease.branch in branches:
            raise LeaseRegistryError(f"Duplicate active lease for branch {lease.branch}")
        if resolved_path in paths:
            raise LeaseRegistryError(f"Duplicate active lease for worktree {resolved_path}")
        tasks.add(lease.task_id)
        branches.add(lease.branch)
        paths.add(resolved_path)


def save_registry(path: Path, registry: LeaseRegistry) -> None:
    _validate_active_uniqueness(registry)
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(registry.to_dict(), indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(path)


def active_lease(registry: LeaseRegistry, task_id: str) -> ExecutionAllocation | None:
    for lease in registry.active:
        if lease.task_id == task_id:
            return lease
    return None


def assert_allocation_available(registry: LeaseRegistry, allocation: ExecutionAllocation) -> None:
    requested_path = str(Path(allocation.worktree_path).resolve())
    for lease in registry.active:
        lease_path = str(Path(lease.worktree_path).resolve())
        if lease.task_id == allocation.task_id:
            raise LeaseCollisionError(
                f"Task {allocation.task_id} already has an active lease at {lease.worktree_path}"
            )
        if lease.branch == allocation.branch:
            raise LeaseCollisionError(
                f"Branch {allocation.branch} already belongs to active task {lease.task_id}"
            )
        if lease_path == requested_path:
            raise LeaseCollisionError(
                f"Worktree {requested_path} already belongs to active task {lease.task_id}"
            )


def acquire_lease(path: Path, allocation: ExecutionAllocation) -> ExecutionAllocation:
    if allocation.lease_status not in {"planned", "active"}:
        raise LeaseRegistryError("Only planned/active allocations can be acquired")
    validate_execution_allocation(allocation)
    registry = load_registry(path, expected_repository=allocation.repository)
    assert_allocation_available(registry, allocation)
    timestamp = _utc_now()
    active = replace(
        allocation,
        lease_status="active",
        updated_at=timestamp,
    )
    save_registry(path, LeaseRegistry(registry.repository, registry.leases + (active,)))
    return active


def release_lease(
    path: Path,
    *,
    repository: str,
    task_id: str,
) -> ExecutionAllocation:
    registry = load_registry(path, expected_repository=repository)
    target = active_lease(registry, task_id)
    if target is None:
        raise LeaseRegistryError(f"No active lease exists for task {task_id}")

    timestamp = _utc_now()
    replacement = replace(target, lease_status="released", updated_at=timestamp)
    leases = tuple(replacement if lease is target else lease for lease in registry.leases)
    save_registry(path, LeaseRegistry(registry.repository, leases))
    return replacement
