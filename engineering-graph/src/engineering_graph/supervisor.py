from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Iterable
import uuid

from .config import GraphSettings
from .execution import ExecutionManifest, validate_execution_manifest
from .orchestrator import select_manifest_tasks
from .runner import (
    RUN_STATUSES,
    AgentRun,
    RunnerRegistry,
    execution_root,
    latest_run,
    load_active_allocation,
    reconcile_registry,
    start_run,
    stop_run,
)
from .worktrees import current_revision

SUPERVISOR_VERSION = "1"
JOB_STATUSES = frozenset({"active", "settled", "stopped"})
TASK_STATUSES = frozenset({"pending", "running", "succeeded", "exhausted", "stopped"})
TASK_TERMINAL_STATUSES = frozenset({"succeeded", "exhausted", "stopped"})
RETRYABLE_RUN_STATUSES = frozenset({"failed", "orphaned"})


class SupervisorError(RuntimeError):
    pass


class SupervisorCollisionError(SupervisorError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class SupervisorTask:
    task_id: str
    status: str
    attempts: int
    run_ids: tuple[str, ...]
    last_run_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "taskId": self.task_id,
            "status": self.status,
            "attempts": self.attempts,
            "runIds": list(self.run_ids),
            "lastRunStatus": self.last_run_status,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SupervisorTask":
        return cls(
            task_id=str(raw.get("taskId") or ""),
            status=str(raw.get("status") or ""),
            attempts=int(raw.get("attempts") or 0),
            run_ids=tuple(str(value) for value in (raw.get("runIds") or [])),
            last_run_status=(
                str(raw["lastRunStatus"])
                if raw.get("lastRunStatus") is not None
                else None
            ),
        )


@dataclass(frozen=True, slots=True)
class SupervisorJob:
    job_id: str
    repository: str
    source_revision: str
    spec_id: str | None
    agent: str
    manifest_path: str
    wave: int
    argv: tuple[str, ...]
    stdin_handoff: bool
    max_parallel: int
    max_attempts: int
    status: str
    tasks: tuple[SupervisorTask, ...]
    created_at: str
    updated_at: str
    finished_at: str | None = None
    supervisor_version: str = SUPERVISOR_VERSION

    @property
    def terminal(self) -> bool:
        return self.status in {"settled", "stopped"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "supervisorVersion": self.supervisor_version,
            "jobId": self.job_id,
            "repository": self.repository,
            "sourceRevision": self.source_revision,
            "specId": self.spec_id,
            "agent": self.agent,
            "manifestPath": self.manifest_path,
            "wave": self.wave,
            "argv": list(self.argv),
            "stdinHandoff": self.stdin_handoff,
            "maxParallel": self.max_parallel,
            "maxAttempts": self.max_attempts,
            "status": self.status,
            "tasks": [task.to_dict() for task in self.tasks],
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "finishedAt": self.finished_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SupervisorJob":
        return cls(
            job_id=str(raw.get("jobId") or ""),
            repository=str(raw.get("repository") or ""),
            source_revision=str(raw.get("sourceRevision") or ""),
            spec_id=str(raw["specId"]) if raw.get("specId") is not None else None,
            agent=str(raw.get("agent") or ""),
            manifest_path=str(raw.get("manifestPath") or ""),
            wave=int(raw.get("wave") or 0),
            argv=tuple(str(value) for value in (raw.get("argv") or [])),
            stdin_handoff=bool(raw.get("stdinHandoff", False)),
            max_parallel=int(raw.get("maxParallel") or 0),
            max_attempts=int(raw.get("maxAttempts") or 0),
            status=str(raw.get("status") or ""),
            tasks=tuple(
                SupervisorTask.from_dict(item)
                for item in (raw.get("tasks") or [])
                if isinstance(item, dict)
            ),
            created_at=str(raw.get("createdAt") or ""),
            updated_at=str(raw.get("updatedAt") or ""),
            finished_at=str(raw["finishedAt"]) if raw.get("finishedAt") is not None else None,
            supervisor_version=str(raw.get("supervisorVersion") or ""),
        )


def validate_supervisor_task(task: SupervisorTask) -> None:
    if not task.task_id.strip():
        raise SupervisorError("Supervisor taskId is required")
    if task.status not in TASK_STATUSES:
        raise SupervisorError(f"Unsupported supervisor task status: {task.status}")
    if task.attempts < 0:
        raise SupervisorError("Supervisor task attempts cannot be negative")
    if task.attempts != len(task.run_ids):
        raise SupervisorError(
            f"Supervisor task attempts/runIds mismatch for {task.task_id}: "
            f"attempts={task.attempts} runIds={len(task.run_ids)}"
        )
    if len(set(task.run_ids)) != len(task.run_ids):
        raise SupervisorError(f"Supervisor task contains duplicate runIds: {task.task_id}")
    if task.last_run_status is not None and task.last_run_status not in RUN_STATUSES:
        raise SupervisorError(
            f"Unsupported last runner status for {task.task_id}: {task.last_run_status}"
        )
    if task.attempts == 0 and task.last_run_status is not None:
        raise SupervisorError(f"Supervisor task without attempts cannot have lastRunStatus: {task.task_id}")


def validate_supervisor_job(job: SupervisorJob) -> None:
    if job.supervisor_version != SUPERVISOR_VERSION:
        raise SupervisorError(f"Unsupported supervisor version: {job.supervisor_version}")
    required = {
        "jobId": job.job_id,
        "repository": job.repository,
        "sourceRevision": job.source_revision,
        "agent": job.agent,
        "manifestPath": job.manifest_path,
        "createdAt": job.created_at,
        "updatedAt": job.updated_at,
    }
    missing = [name for name, value in required.items() if not value.strip()]
    if missing:
        raise SupervisorError(f"Supervisor job missing required fields: {', '.join(missing)}")
    if job.wave < 1:
        raise SupervisorError("Supervisor wave index must be positive")
    if not job.argv:
        raise SupervisorError("Supervisor argv cannot be empty")
    if job.max_parallel < 1:
        raise SupervisorError("Supervisor maxParallel must be at least 1")
    if job.max_attempts < 1:
        raise SupervisorError("Supervisor maxAttempts must be at least 1")
    if job.status not in JOB_STATUSES:
        raise SupervisorError(f"Unsupported supervisor job status: {job.status}")
    if not job.tasks:
        raise SupervisorError("Supervisor job requires at least one task")
    task_ids = [task.task_id for task in job.tasks]
    if len(set(task_ids)) != len(task_ids):
        raise SupervisorError("Supervisor job contains duplicate task ids")
    for task in job.tasks:
        validate_supervisor_task(task)
        if task.attempts > job.max_attempts:
            raise SupervisorError(
                f"Supervisor task {task.task_id} exceeds maxAttempts={job.max_attempts}"
            )
    if job.status == "active" and job.finished_at is not None:
        raise SupervisorError("Active supervisor job cannot have finishedAt")
    if job.status != "active" and not job.finished_at:
        raise SupervisorError("Terminal supervisor job requires finishedAt")


def supervisor_root(settings: GraphSettings, override: Path | None = None) -> Path:
    return execution_root(settings, override) / "supervisor"


def supervisor_jobs_root(settings: GraphSettings, override: Path | None = None) -> Path:
    return supervisor_root(settings, override) / "jobs"


def supervisor_job_path(
    settings: GraphSettings,
    job_id: str,
    override: Path | None = None,
) -> Path:
    if not job_id.strip() or "/" in job_id or "\\" in job_id:
        raise SupervisorError("Invalid supervisor job id")
    return supervisor_jobs_root(settings, override) / f"{job_id}.json"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def save_supervisor_job(
    settings: GraphSettings,
    job: SupervisorJob,
    *,
    root_override: Path | None = None,
) -> None:
    validate_supervisor_job(job)
    _atomic_json(supervisor_job_path(settings, job.job_id, root_override), job.to_dict())


def load_supervisor_job(
    settings: GraphSettings,
    job_id: str,
    *,
    root_override: Path | None = None,
) -> SupervisorJob:
    path = supervisor_job_path(settings, job_id, root_override)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SupervisorError(f"Supervisor job not found: {job_id}") from error
    except json.JSONDecodeError as error:
        raise SupervisorError(f"Supervisor job is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise SupervisorError("Supervisor job root must be a JSON object")
    job = SupervisorJob.from_dict(raw)
    validate_supervisor_job(job)
    if job.job_id != job_id:
        raise SupervisorError(
            f"Supervisor jobId mismatch: expected={job_id} actual={job.job_id}"
        )
    if job.repository != settings.repository_id:
        raise SupervisorError(
            f"Supervisor repository mismatch: expected={settings.repository_id!r} actual={job.repository!r}"
        )
    return job


def list_supervisor_jobs(
    settings: GraphSettings,
    *,
    root_override: Path | None = None,
) -> tuple[SupervisorJob, ...]:
    root = supervisor_jobs_root(settings, root_override)
    if not root.is_dir():
        return ()
    jobs = tuple(
        load_supervisor_job(settings, path.stem, root_override=root_override)
        for path in sorted(root.glob("*.json"))
    )
    return tuple(sorted(jobs, key=lambda job: (job.created_at, job.job_id)))


def _replace_task(job: SupervisorJob, replacement: SupervisorTask) -> SupervisorJob:
    tasks = tuple(
        replacement if task.task_id == replacement.task_id else task
        for task in job.tasks
    )
    return replace(job, tasks=tasks, updated_at=_utc_now())


def _runs_by_id(registry: RunnerRegistry) -> dict[str, AgentRun]:
    return {run.run_id: run for run in registry.runs}


def _reconcile_job(job: SupervisorJob, registry: RunnerRegistry) -> SupervisorJob:
    if job.status == "stopped":
        return job
    by_id = _runs_by_id(registry)
    changed = False
    tasks: list[SupervisorTask] = []
    for task in job.tasks:
        if not task.run_ids:
            tasks.append(task)
            continue
        run_id = task.run_ids[-1]
        run = by_id.get(run_id)
        if run is None:
            raise SupervisorError(
                f"Supervisor job {job.job_id} owns missing runner {run_id} for {task.task_id}; refusing to guess"
            )
        if run.task_id != task.task_id:
            raise SupervisorError(
                f"Supervisor runner ownership mismatch: run={run_id} expectedTask={task.task_id} actualTask={run.task_id}"
            )
        if run.repository != job.repository or run.source_revision != job.source_revision:
            raise SupervisorError(
                f"Supervisor runner identity mismatch for {task.task_id}: repository/revision changed"
            )

        if run.status == "running":
            status = "running"
        elif run.status == "succeeded":
            status = "succeeded"
        elif run.status == "stopped":
            status = "stopped"
        elif run.status in RETRYABLE_RUN_STATUSES:
            status = "pending" if task.attempts < job.max_attempts else "exhausted"
        else:
            raise SupervisorError(f"Unsupported runner status during supervisor reconciliation: {run.status}")

        refreshed = replace(task, status=status, last_run_status=run.status)
        changed = changed or refreshed != task
        tasks.append(refreshed)

    status = job.status
    finished_at = job.finished_at
    if status == "active" and all(task.status in TASK_TERMINAL_STATUSES for task in tasks):
        status = "settled"
        finished_at = finished_at or _utc_now()
        changed = True

    if not changed:
        return job
    return replace(
        job,
        tasks=tuple(tasks),
        status=status,
        finished_at=finished_at,
        updated_at=_utc_now(),
    )


def refresh_supervisor_job(
    settings: GraphSettings,
    job_id: str,
    *,
    root_override: Path | None = None,
) -> SupervisorJob:
    job = load_supervisor_job(settings, job_id, root_override=root_override)
    registry = reconcile_registry(settings, root_override=root_override)
    refreshed = _reconcile_job(job, registry)
    if refreshed != job:
        save_supervisor_job(settings, refreshed, root_override=root_override)
    return refreshed


def _validate_manifest_for_supervision(
    settings: GraphSettings,
    manifest: ExecutionManifest,
    wave: int,
) -> tuple[str, ...]:
    validate_execution_manifest(manifest)
    if manifest.cycles:
        rendered = "; ".join(" -> ".join(cycle) for cycle in manifest.cycles)
        raise SupervisorError(f"Execution manifest contains task dependency cycles: {rendered}")
    if manifest.repository != settings.repository_id:
        raise SupervisorError(
            f"Execution manifest repository mismatch: manifest={manifest.repository!r} expected={settings.repository_id!r}"
        )
    revision = current_revision(settings.repo_root)
    if manifest.source_revision != revision:
        raise SupervisorError(
            f"Execution manifest is stale: manifest={manifest.source_revision} HEAD={revision}"
        )
    return select_manifest_tasks(manifest, wave=wave)


def _validate_active_allocations(
    settings: GraphSettings,
    manifest: ExecutionManifest,
    task_ids: Iterable[str],
    *,
    root_override: Path | None,
) -> None:
    for task_id in task_ids:
        allocation = load_active_allocation(settings, task_id, root_override=root_override)
        if allocation.repository != manifest.repository:
            raise SupervisorError(
                f"Allocation repository mismatch for {task_id}: {allocation.repository!r}"
            )
        if allocation.source_revision != manifest.source_revision:
            raise SupervisorError(
                f"Allocation revision mismatch for {task_id}: allocation={allocation.source_revision} manifest={manifest.source_revision}"
            )
        if allocation.agent != manifest.agent:
            raise SupervisorError(
                f"Allocation agent mismatch for {task_id}: allocation={allocation.agent} manifest={manifest.agent}"
            )
        if allocation.lease_status != "active":
            raise SupervisorError(
                f"Allocation is not active for {task_id}: {allocation.lease_status}"
            )


def _refresh_existing_jobs(
    settings: GraphSettings,
    registry: RunnerRegistry,
    *,
    root_override: Path | None,
) -> tuple[SupervisorJob, ...]:
    values: list[SupervisorJob] = []
    for job in list_supervisor_jobs(settings, root_override=root_override):
        refreshed = _reconcile_job(job, registry) if job.status == "active" else job
        if refreshed != job:
            save_supervisor_job(settings, refreshed, root_override=root_override)
        values.append(refreshed)
    return tuple(values)


def create_supervisor_job(
    settings: GraphSettings,
    manifest: ExecutionManifest,
    manifest_path: Path,
    wave: int,
    argv: Iterable[str],
    *,
    max_parallel: int = 1,
    max_attempts: int = 1,
    stdin_handoff: bool = False,
    root_override: Path | None = None,
) -> SupervisorJob:
    command = tuple(str(value) for value in argv)
    if not command:
        raise SupervisorError("Supervisor command argv cannot be empty")
    if max_parallel < 1:
        raise SupervisorError("Supervisor maxParallel must be at least 1")
    if max_attempts < 1:
        raise SupervisorError("Supervisor maxAttempts must be at least 1")

    selected = _validate_manifest_for_supervision(settings, manifest, wave)
    _validate_active_allocations(
        settings,
        manifest,
        selected,
        root_override=root_override,
    )

    registry = reconcile_registry(settings, root_override=root_override)
    existing_jobs = _refresh_existing_jobs(
        settings,
        registry,
        root_override=root_override,
    )
    selected_set = set(selected)
    for existing in existing_jobs:
        if existing.status != "active":
            continue
        overlap = selected_set & {task.task_id for task in existing.tasks}
        if overlap:
            raise SupervisorCollisionError(
                f"Tasks already owned by active supervisor {existing.job_id}: {', '.join(sorted(overlap))}"
            )

    for task_id in selected:
        run = latest_run(registry, task_id)
        if run is not None and not run.terminal:
            raise SupervisorCollisionError(
                f"Task {task_id} already has non-terminal runner {run.run_id} outside the new supervisor job"
            )

    now = _utc_now()
    job = SupervisorJob(
        job_id=uuid.uuid4().hex,
        repository=manifest.repository,
        source_revision=manifest.source_revision,
        spec_id=manifest.spec_id,
        agent=manifest.agent,
        manifest_path=str(manifest_path.resolve()),
        wave=wave,
        argv=command,
        stdin_handoff=stdin_handoff,
        max_parallel=max_parallel,
        max_attempts=max_attempts,
        status="active",
        tasks=tuple(
            SupervisorTask(
                task_id=task_id,
                status="pending",
                attempts=0,
                run_ids=(),
            )
            for task_id in selected
        ),
        created_at=now,
        updated_at=now,
    )
    save_supervisor_job(settings, job, root_override=root_override)
    return job


def supervisor_tick(
    settings: GraphSettings,
    job_id: str,
    *,
    root_override: Path | None = None,
) -> SupervisorJob:
    job = refresh_supervisor_job(settings, job_id, root_override=root_override)
    if job.status != "active":
        return job

    running = sum(task.status == "running" for task in job.tasks)
    slots = max(job.max_parallel - running, 0)
    if slots == 0:
        return job

    current = job
    for task in current.tasks:
        if slots <= 0:
            break
        latest_task = next(item for item in current.tasks if item.task_id == task.task_id)
        if latest_task.status != "pending":
            continue
        if latest_task.attempts >= current.max_attempts:
            exhausted = replace(latest_task, status="exhausted")
            current = _replace_task(current, exhausted)
            save_supervisor_job(settings, current, root_override=root_override)
            continue

        run = start_run(
            settings,
            latest_task.task_id,
            current.argv,
            stdin_handoff=current.stdin_handoff,
            root_override=root_override,
        )
        launched = replace(
            latest_task,
            status="running",
            attempts=latest_task.attempts + 1,
            run_ids=latest_task.run_ids + (run.run_id,),
            last_run_status=run.status,
        )
        current = _replace_task(current, launched)
        save_supervisor_job(settings, current, root_override=root_override)
        slots -= 1

    return current


def start_supervisor_job(
    settings: GraphSettings,
    manifest: ExecutionManifest,
    manifest_path: Path,
    wave: int,
    argv: Iterable[str],
    *,
    max_parallel: int = 1,
    max_attempts: int = 1,
    stdin_handoff: bool = False,
    root_override: Path | None = None,
) -> SupervisorJob:
    job = create_supervisor_job(
        settings,
        manifest,
        manifest_path,
        wave,
        argv,
        max_parallel=max_parallel,
        max_attempts=max_attempts,
        stdin_handoff=stdin_handoff,
        root_override=root_override,
    )
    return supervisor_tick(settings, job.job_id, root_override=root_override)


def status_supervisor_jobs(
    settings: GraphSettings,
    *,
    job_id: str | None = None,
    root_override: Path | None = None,
) -> tuple[SupervisorJob, ...]:
    if job_id is not None:
        return (refresh_supervisor_job(settings, job_id, root_override=root_override),)
    jobs = list_supervisor_jobs(settings, root_override=root_override)
    refreshed: list[SupervisorJob] = []
    for job in jobs:
        if job.status == "active":
            refreshed.append(
                refresh_supervisor_job(settings, job.job_id, root_override=root_override)
            )
        else:
            refreshed.append(job)
    return tuple(refreshed)


def stop_supervisor_job(
    settings: GraphSettings,
    job_id: str,
    *,
    root_override: Path | None = None,
    timeout_seconds: float = 5.0,
    force: bool = False,
) -> SupervisorJob:
    job = refresh_supervisor_job(settings, job_id, root_override=root_override)
    if job.terminal:
        return job

    current = job
    for task in tuple(current.tasks):
        latest_task = next(item for item in current.tasks if item.task_id == task.task_id)
        if latest_task.status != "running":
            continue
        registry = reconcile_registry(settings, root_override=root_override)
        latest = latest_run(registry, latest_task.task_id)
        owned_run_id = latest_task.run_ids[-1] if latest_task.run_ids else None
        if latest is None or latest.run_id != owned_run_id:
            raise SupervisorError(
                f"Supervisor stop ownership mismatch for {latest_task.task_id}: "
                f"owned={owned_run_id or '-'} latest={latest.run_id if latest else '-'}"
            )
        stopped = stop_run(
            settings,
            latest_task.task_id,
            root_override=root_override,
            timeout_seconds=timeout_seconds,
            force=force,
        )
        updated_task = replace(
            latest_task,
            status="stopped" if stopped.status == "stopped" else latest_task.status,
            last_run_status=stopped.status,
        )
        current = _replace_task(current, updated_task)
        save_supervisor_job(settings, current, root_override=root_override)

    now = _utc_now()
    stopped_tasks = tuple(
        task
        if task.status in TASK_TERMINAL_STATUSES
        else replace(task, status="stopped")
        for task in current.tasks
    )
    current = replace(
        current,
        tasks=stopped_tasks,
        status="stopped",
        finished_at=now,
        updated_at=now,
    )
    save_supervisor_job(settings, current, root_override=root_override)
    return current
