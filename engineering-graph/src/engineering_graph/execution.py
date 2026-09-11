from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .agent_adapters import SUPPORTED_AGENTS
from .planner import ExecutionPlan

MANIFEST_VERSION = "1"
ALLOCATION_VERSION = "1"
LEASE_STATUSES = frozenset({"planned", "active", "released"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class ExecutionWave:
    index: int
    tasks: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"index": self.index, "tasks": list(self.tasks)}


@dataclass(frozen=True, slots=True)
class ExecutionConflict:
    left: str
    right: str
    artifacts: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "left": self.left,
            "right": self.right,
            "artifacts": list(self.artifacts),
        }


@dataclass(frozen=True, slots=True)
class ExecutionManifest:
    repository: str
    source_revision: str
    spec_id: str | None
    agent: str
    ready: tuple[str, ...]
    blocked: tuple[tuple[str, tuple[str, ...]], ...]
    cycles: tuple[tuple[str, ...], ...]
    conflicts: tuple[ExecutionConflict, ...]
    waves: tuple[ExecutionWave, ...]
    generated_at: str
    manifest_version: str = MANIFEST_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifestVersion": self.manifest_version,
            "repository": self.repository,
            "sourceRevision": self.source_revision,
            "specId": self.spec_id,
            "agent": self.agent,
            "generatedAt": self.generated_at,
            "ready": list(self.ready),
            "blocked": [
                {"task": task, "blockedBy": list(blockers)}
                for task, blockers in self.blocked
            ],
            "cycles": [list(cycle) for cycle in self.cycles],
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
            "waves": [wave.to_dict() for wave in self.waves],
        }

    def semantic_dict(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("generatedAt", None)
        return payload

    def semantic_json(self) -> str:
        return json.dumps(self.semantic_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ExecutionManifest":
        blocked_raw = raw.get("blocked") or []
        conflicts_raw = raw.get("conflicts") or []
        waves_raw = raw.get("waves") or []
        return cls(
            repository=str(raw.get("repository") or ""),
            source_revision=str(raw.get("sourceRevision") or ""),
            spec_id=str(raw["specId"]) if raw.get("specId") is not None else None,
            agent=str(raw.get("agent") or ""),
            ready=tuple(str(value) for value in (raw.get("ready") or [])),
            blocked=tuple(
                (
                    str(item.get("task") or ""),
                    tuple(str(value) for value in (item.get("blockedBy") or [])),
                )
                for item in blocked_raw
                if isinstance(item, dict)
            ),
            cycles=tuple(
                tuple(str(value) for value in cycle)
                for cycle in (raw.get("cycles") or [])
                if isinstance(cycle, list)
            ),
            conflicts=tuple(
                ExecutionConflict(
                    left=str(item.get("left") or ""),
                    right=str(item.get("right") or ""),
                    artifacts=tuple(str(value) for value in (item.get("artifacts") or [])),
                )
                for item in conflicts_raw
                if isinstance(item, dict)
            ),
            waves=tuple(
                ExecutionWave(
                    index=int(item.get("index") or 0),
                    tasks=tuple(str(value) for value in (item.get("tasks") or [])),
                )
                for item in waves_raw
                if isinstance(item, dict)
            ),
            generated_at=str(raw.get("generatedAt") or ""),
            manifest_version=str(raw.get("manifestVersion") or ""),
        )


@dataclass(frozen=True, slots=True)
class ExecutionAllocation:
    repository: str
    task_id: str
    spec_id: str
    source_revision: str
    agent: str
    branch: str
    worktree_path: str
    context_path: str
    handoff_path: str
    lease_status: str
    validation_commands: tuple[str, ...]
    created_at: str
    updated_at: str
    allocation_version: str = ALLOCATION_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "allocationVersion": self.allocation_version,
            "repository": self.repository,
            "taskId": self.task_id,
            "specId": self.spec_id,
            "sourceRevision": self.source_revision,
            "agent": self.agent,
            "branch": self.branch,
            "worktreePath": self.worktree_path,
            "contextPath": self.context_path,
            "handoffPath": self.handoff_path,
            "leaseStatus": self.lease_status,
            "validationCommands": list(self.validation_commands),
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ExecutionAllocation":
        return cls(
            repository=str(raw.get("repository") or ""),
            task_id=str(raw.get("taskId") or ""),
            spec_id=str(raw.get("specId") or ""),
            source_revision=str(raw.get("sourceRevision") or ""),
            agent=str(raw.get("agent") or ""),
            branch=str(raw.get("branch") or ""),
            worktree_path=str(raw.get("worktreePath") or ""),
            context_path=str(raw.get("contextPath") or ""),
            handoff_path=str(raw.get("handoffPath") or ""),
            lease_status=str(raw.get("leaseStatus") or ""),
            validation_commands=tuple(str(value) for value in (raw.get("validationCommands") or [])),
            created_at=str(raw.get("createdAt") or ""),
            updated_at=str(raw.get("updatedAt") or ""),
            allocation_version=str(raw.get("allocationVersion") or ""),
        )


def build_execution_manifest(
    plan: ExecutionPlan,
    *,
    repository: str,
    source_revision: str,
    spec_id: str | None,
    agent: str,
    generated_at: str | None = None,
) -> ExecutionManifest:
    if agent not in SUPPORTED_AGENTS:
        raise ValueError(f"Unsupported agent adapter: {agent}")
    return ExecutionManifest(
        repository=repository,
        source_revision=source_revision,
        spec_id=spec_id,
        agent=agent,
        ready=plan.ready,
        blocked=plan.blocked,
        cycles=plan.cycles,
        conflicts=tuple(
            ExecutionConflict(conflict.left, conflict.right, conflict.artifacts)
            for conflict in plan.conflicts
        ),
        waves=tuple(
            ExecutionWave(index=index, tasks=tuple(tasks))
            for index, tasks in enumerate(plan.waves, start=1)
        ),
        generated_at=generated_at or _utc_now(),
    )


def validate_execution_manifest(manifest: ExecutionManifest) -> None:
    if manifest.manifest_version != MANIFEST_VERSION:
        raise ValueError(f"Unsupported execution manifest version: {manifest.manifest_version}")
    if not manifest.repository.strip():
        raise ValueError("Execution manifest repository is required")
    if not manifest.source_revision.strip():
        raise ValueError("Execution manifest sourceRevision is required")
    if not manifest.generated_at.strip():
        raise ValueError("Execution manifest generatedAt is required")
    if manifest.agent not in SUPPORTED_AGENTS:
        raise ValueError(f"Unsupported execution manifest agent: {manifest.agent}")

    expected_indexes = tuple(range(1, len(manifest.waves) + 1))
    actual_indexes = tuple(wave.index for wave in manifest.waves)
    if actual_indexes != expected_indexes:
        raise ValueError("Execution manifest wave indexes must be contiguous starting at 1")

    seen_tasks: set[str] = set()
    for wave in manifest.waves:
        if not wave.tasks:
            raise ValueError(f"Execution wave {wave.index} cannot be empty")
        if tuple(sorted(set(wave.tasks))) != tuple(sorted(wave.tasks)):
            raise ValueError(f"Execution wave {wave.index} contains duplicate tasks")
        overlap = seen_tasks & set(wave.tasks)
        if overlap:
            raise ValueError(f"Tasks appear in multiple execution waves: {', '.join(sorted(overlap))}")
        seen_tasks.update(wave.tasks)

    for task, blockers in manifest.blocked:
        if not task or not blockers:
            raise ValueError("Blocked execution tasks must include task and blockers")

    for conflict in manifest.conflicts:
        if not conflict.left or not conflict.right or not conflict.artifacts:
            raise ValueError("Execution conflicts require both tasks and at least one artifact")


def load_execution_manifest(path: Path) -> ExecutionManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"Execution manifest not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Execution manifest is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise ValueError("Execution manifest root must be a JSON object")
    manifest = ExecutionManifest.from_dict(raw)
    validate_execution_manifest(manifest)
    return manifest


def write_execution_manifest(manifest: ExecutionManifest, output: Path) -> str:
    validate_execution_manifest(manifest)
    rendered = json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    return rendered


def planned_allocation(
    *,
    repository: str,
    task_id: str,
    spec_id: str,
    source_revision: str,
    agent: str,
    branch: str,
    worktree_path: str,
    context_path: str,
    handoff_path: str,
    validation_commands: tuple[str, ...] = (),
    now: str | None = None,
) -> ExecutionAllocation:
    timestamp = now or _utc_now()
    return ExecutionAllocation(
        repository=repository,
        task_id=task_id,
        spec_id=spec_id,
        source_revision=source_revision,
        agent=agent,
        branch=branch,
        worktree_path=worktree_path,
        context_path=context_path,
        handoff_path=handoff_path,
        lease_status="planned",
        validation_commands=validation_commands,
        created_at=timestamp,
        updated_at=timestamp,
    )


def validate_execution_allocation(allocation: ExecutionAllocation) -> None:
    if allocation.allocation_version != ALLOCATION_VERSION:
        raise ValueError(f"Unsupported execution allocation version: {allocation.allocation_version}")
    required = {
        "repository": allocation.repository,
        "taskId": allocation.task_id,
        "specId": allocation.spec_id,
        "sourceRevision": allocation.source_revision,
        "agent": allocation.agent,
        "branch": allocation.branch,
        "worktreePath": allocation.worktree_path,
        "contextPath": allocation.context_path,
        "handoffPath": allocation.handoff_path,
        "createdAt": allocation.created_at,
        "updatedAt": allocation.updated_at,
    }
    missing = [name for name, value in required.items() if not value.strip()]
    if missing:
        raise ValueError(f"Execution allocation missing required fields: {', '.join(missing)}")
    if allocation.agent not in SUPPORTED_AGENTS:
        raise ValueError(f"Unsupported execution allocation agent: {allocation.agent}")
    if allocation.lease_status not in LEASE_STATUSES:
        raise ValueError(f"Unsupported execution lease status: {allocation.lease_status}")
