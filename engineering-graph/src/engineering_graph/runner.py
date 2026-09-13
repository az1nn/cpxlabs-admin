from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any, Iterable
import uuid

from .config import GraphSettings
from .execution import ExecutionAllocation
from .leases import LeaseRegistryError, active_lease, load_registry
from .worktrees import current_revision, find_worktree, list_worktrees

RUN_VERSION = "1"
RUNNER_REGISTRY_VERSION = "1"
RESULT_VERSION = "1"
TERMINAL_STATUSES = frozenset({"succeeded", "failed", "stopped", "orphaned"})
RUN_STATUSES = frozenset({"running", *TERMINAL_STATUSES})


class RunnerError(RuntimeError):
    pass


class RunnerCollisionError(RunnerError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class AgentRun:
    run_id: str
    repository: str
    task_id: str
    spec_id: str
    source_revision: str
    agent: str
    branch: str
    worktree_path: str
    handoff_path: str
    context_path: str
    argv: tuple[str, ...]
    stdin_handoff: bool
    pid: int | None
    process_fingerprint: str | None
    process_group_id: int | None
    status: str
    exit_code: int | None
    stop_requested: bool
    stdout_path: str
    stderr_path: str
    result_path: str
    created_at: str
    started_at: str | None
    finished_at: str | None
    updated_at: str
    run_version: str = RUN_VERSION

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    def to_dict(self) -> dict[str, Any]:
        return {
            "runVersion": self.run_version,
            "runId": self.run_id,
            "repository": self.repository,
            "taskId": self.task_id,
            "specId": self.spec_id,
            "sourceRevision": self.source_revision,
            "agent": self.agent,
            "branch": self.branch,
            "worktreePath": self.worktree_path,
            "handoffPath": self.handoff_path,
            "contextPath": self.context_path,
            "argv": list(self.argv),
            "stdinHandoff": self.stdin_handoff,
            "pid": self.pid,
            "processFingerprint": self.process_fingerprint,
            "processGroupId": self.process_group_id,
            "status": self.status,
            "exitCode": self.exit_code,
            "stopRequested": self.stop_requested,
            "stdoutPath": self.stdout_path,
            "stderrPath": self.stderr_path,
            "resultPath": self.result_path,
            "createdAt": self.created_at,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "updatedAt": self.updated_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "AgentRun":
        return cls(
            run_id=str(raw.get("runId") or ""),
            repository=str(raw.get("repository") or ""),
            task_id=str(raw.get("taskId") or ""),
            spec_id=str(raw.get("specId") or ""),
            source_revision=str(raw.get("sourceRevision") or ""),
            agent=str(raw.get("agent") or ""),
            branch=str(raw.get("branch") or ""),
            worktree_path=str(raw.get("worktreePath") or ""),
            handoff_path=str(raw.get("handoffPath") or ""),
            context_path=str(raw.get("contextPath") or ""),
            argv=tuple(str(value) for value in (raw.get("argv") or [])),
            stdin_handoff=bool(raw.get("stdinHandoff", False)),
            pid=int(raw["pid"]) if raw.get("pid") is not None else None,
            process_fingerprint=(
                str(raw["processFingerprint"])
                if raw.get("processFingerprint") is not None
                else None
            ),
            process_group_id=(
                int(raw["processGroupId"])
                if raw.get("processGroupId") is not None
                else None
            ),
            status=str(raw.get("status") or ""),
            exit_code=int(raw["exitCode"]) if raw.get("exitCode") is not None else None,
            stop_requested=bool(raw.get("stopRequested", False)),
            stdout_path=str(raw.get("stdoutPath") or ""),
            stderr_path=str(raw.get("stderrPath") or ""),
            result_path=str(raw.get("resultPath") or ""),
            created_at=str(raw.get("createdAt") or ""),
            started_at=str(raw["startedAt"]) if raw.get("startedAt") is not None else None,
            finished_at=str(raw["finishedAt"]) if raw.get("finishedAt") is not None else None,
            updated_at=str(raw.get("updatedAt") or ""),
            run_version=str(raw.get("runVersion") or ""),
        )


@dataclass(frozen=True, slots=True)
class RunnerRegistry:
    repository: str
    runs: tuple[AgentRun, ...]
    registry_version: str = RUNNER_REGISTRY_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "registryVersion": self.registry_version,
            "repository": self.repository,
            "runs": [run.to_dict() for run in self.runs],
        }


@dataclass(frozen=True, slots=True)
class RunnerExitResult:
    run_id: str
    exit_code: int
    finished_at: str
    result_version: str = RESULT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "resultVersion": self.result_version,
            "runId": self.run_id,
            "exitCode": self.exit_code,
            "finishedAt": self.finished_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RunnerExitResult":
        return cls(
            run_id=str(raw.get("runId") or ""),
            exit_code=int(raw.get("exitCode")),
            finished_at=str(raw.get("finishedAt") or ""),
            result_version=str(raw.get("resultVersion") or ""),
        )


def validate_run(run: AgentRun) -> None:
    if run.run_version != RUN_VERSION:
        raise RunnerError(f"Unsupported run version: {run.run_version}")
    required = {
        "runId": run.run_id,
        "repository": run.repository,
        "taskId": run.task_id,
        "specId": run.spec_id,
        "sourceRevision": run.source_revision,
        "agent": run.agent,
        "branch": run.branch,
        "worktreePath": run.worktree_path,
        "handoffPath": run.handoff_path,
        "contextPath": run.context_path,
        "stdoutPath": run.stdout_path,
        "stderrPath": run.stderr_path,
        "resultPath": run.result_path,
        "createdAt": run.created_at,
        "updatedAt": run.updated_at,
    }
    missing = [name for name, value in required.items() if not value.strip()]
    if missing:
        raise RunnerError(f"Agent run missing required fields: {', '.join(missing)}")
    if not run.argv:
        raise RunnerError("Agent run argv cannot be empty")
    if run.status not in RUN_STATUSES:
        raise RunnerError(f"Unsupported agent run status: {run.status}")
    if run.status == "running" and run.pid is None:
        raise RunnerError("Running agent run requires pid")


def validate_registry(registry: RunnerRegistry) -> None:
    if registry.registry_version != RUNNER_REGISTRY_VERSION:
        raise RunnerError(f"Unsupported runner registry version: {registry.registry_version}")
    seen_ids: set[str] = set()
    active_tasks: set[str] = set()
    for run in registry.runs:
        validate_run(run)
        if run.run_id in seen_ids:
            raise RunnerError(f"Duplicate runner runId: {run.run_id}")
        seen_ids.add(run.run_id)
        if not run.terminal:
            if run.task_id in active_tasks:
                raise RunnerError(f"Duplicate non-terminal run for task {run.task_id}")
            active_tasks.add(run.task_id)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def execution_root(settings: GraphSettings, override: Path | None = None) -> Path:
    return (override or settings.tool_root / ".execution").resolve()


def runs_root(settings: GraphSettings, override: Path | None = None) -> Path:
    return execution_root(settings, override) / "runs"


def registry_path(settings: GraphSettings, override: Path | None = None) -> Path:
    return runs_root(settings, override) / "registry.json"


def load_runner_registry(path: Path, *, expected_repository: str) -> RunnerRegistry:
    if not path.exists():
        return RunnerRegistry(expected_repository, ())
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RunnerError(f"Runner registry is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise RunnerError("Runner registry root must be a JSON object")
    registry = RunnerRegistry(
        repository=str(raw.get("repository") or ""),
        runs=tuple(
            AgentRun.from_dict(item)
            for item in (raw.get("runs") or [])
            if isinstance(item, dict)
        ),
        registry_version=str(raw.get("registryVersion") or ""),
    )
    if registry.repository != expected_repository:
        raise RunnerError(
            f"Runner registry repository mismatch: expected={expected_repository!r} actual={registry.repository!r}"
        )
    validate_registry(registry)
    return registry


def save_runner_registry(path: Path, registry: RunnerRegistry) -> None:
    validate_registry(registry)
    _atomic_json(path, registry.to_dict())


def _save_run_files(path: Path, registry: RunnerRegistry, run: AgentRun) -> None:
    save_runner_registry(path, registry)
    _atomic_json(Path(run.stdout_path).parent / "run.json", run.to_dict())


def latest_run(registry: RunnerRegistry, task_id: str) -> AgentRun | None:
    candidates = [run for run in registry.runs if run.task_id == task_id]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item.created_at, item.run_id))[-1]


def _replace_run(registry: RunnerRegistry, replacement: AgentRun) -> RunnerRegistry:
    runs = tuple(replacement if run.run_id == replacement.run_id else run for run in registry.runs)
    return RunnerRegistry(registry.repository, runs, registry.registry_version)


def load_active_allocation(
    settings: GraphSettings,
    task_id: str,
    *,
    root_override: Path | None = None,
) -> ExecutionAllocation:
    root = execution_root(settings, root_override)
    lease_registry = load_registry(root / "leases.json", expected_repository=settings.repository_id)
    allocation = active_lease(lease_registry, task_id)
    if allocation is None:
        raise LeaseRegistryError(f"No active lease exists for task {task_id}")
    return allocation


def validate_allocation_for_run(
    settings: GraphSettings,
    allocation: ExecutionAllocation,
) -> None:
    if allocation.repository != settings.repository_id:
        raise RunnerError(
            f"Allocation repository mismatch: allocation={allocation.repository!r} expected={settings.repository_id!r}"
        )
    revision = current_revision(settings.repo_root)
    if allocation.source_revision != revision:
        raise RunnerError(
            f"Allocation is stale: allocation={allocation.source_revision} HEAD={revision}; replan/reprepare before running"
        )
    worktree_path = Path(allocation.worktree_path).resolve()
    descriptor = find_worktree(list_worktrees(settings.repo_root), path=worktree_path)
    if descriptor is None:
        raise RunnerError(f"Allocated worktree is not registered with Git: {worktree_path}")
    if descriptor.branch != allocation.branch:
        raise RunnerError(
            f"Allocated worktree branch mismatch: expected={allocation.branch} actual={descriptor.branch}"
        )
    if not worktree_path.is_dir():
        raise RunnerError(f"Allocated worktree does not exist: {worktree_path}")
    if not Path(allocation.handoff_path).is_file():
        raise RunnerError(f"Allocation handoff does not exist: {allocation.handoff_path}")


_PLACEHOLDERS = {
    "task_id": lambda a: a.task_id,
    "spec_id": lambda a: a.spec_id,
    "worktree": lambda a: a.worktree_path,
    "handoff": lambda a: a.handoff_path,
    "context": lambda a: a.context_path,
    "branch": lambda a: a.branch,
    "source_revision": lambda a: a.source_revision,
}


def expand_command(argv: Iterable[str], allocation: ExecutionAllocation) -> tuple[str, ...]:
    values = tuple(str(value) for value in argv)
    if not values:
        raise RunnerError("Runner command argv cannot be empty")
    expanded: list[str] = []
    for token in values:
        rendered = token
        for name, getter in _PLACEHOLDERS.items():
            rendered = rendered.replace("{" + name + "}", getter(allocation))
        expanded.append(rendered)
    return tuple(expanded)


def process_fingerprint(pid: int) -> str | None:
    stat = Path(f"/proc/{pid}/stat")
    if not stat.is_file():
        return None
    try:
        value = stat.read_text(encoding="utf-8")
        close = value.rfind(")")
        if close < 0:
            return None
        fields = value[close + 2 :].split()
        start_time = fields[19]
        return f"linux-proc:{pid}:{start_time}"
    except (OSError, IndexError):
        return None


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def process_identity_matches(run: AgentRun) -> bool:
    if run.pid is None:
        return False
    if not process_alive(run.pid):
        return False
    if run.process_fingerprint is None:
        return True
    current = process_fingerprint(run.pid)
    return current == run.process_fingerprint


def _load_result(path: Path, run_id: str) -> RunnerExitResult | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RunnerError(f"Runner result is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise RunnerError("Runner result root must be a JSON object")
    result = RunnerExitResult.from_dict(raw)
    if result.result_version != RESULT_VERSION:
        raise RunnerError(f"Unsupported runner result version: {result.result_version}")
    if result.run_id != run_id:
        raise RunnerError(f"Runner result runId mismatch: expected={run_id} actual={result.run_id}")
    if not result.finished_at:
        raise RunnerError("Runner result finishedAt is required")
    return result


def refresh_run(
    settings: GraphSettings,
    run: AgentRun,
    *,
    root_override: Path | None = None,
) -> AgentRun:
    if run.terminal:
        return run
    result = _load_result(Path(run.result_path), run.run_id)
    now = _utc_now()
    if result is not None:
        status = "stopped" if run.stop_requested else ("succeeded" if result.exit_code == 0 else "failed")
        return replace(
            run,
            status=status,
            exit_code=result.exit_code,
            finished_at=result.finished_at,
            updated_at=now,
        )
    if run.pid is not None and process_identity_matches(run):
        return run
    return replace(
        run,
        status="stopped" if run.stop_requested else "orphaned",
        finished_at=run.finished_at or now,
        updated_at=now,
    )


def reconcile_registry(
    settings: GraphSettings,
    *,
    root_override: Path | None = None,
) -> RunnerRegistry:
    path = registry_path(settings, root_override)
    registry = load_runner_registry(path, expected_repository=settings.repository_id)
    changed = False
    runs: list[AgentRun] = []
    for run in registry.runs:
        refreshed = refresh_run(settings, run, root_override=root_override)
        if refreshed != run:
            changed = True
        runs.append(refreshed)
    if not changed:
        return registry
    updated = RunnerRegistry(registry.repository, tuple(runs), registry.registry_version)
    save_runner_registry(path, updated)
    for run in updated.runs:
        _atomic_json(Path(run.stdout_path).parent / "run.json", run.to_dict())
    return updated


def start_run(
    settings: GraphSettings,
    task_id: str,
    argv: Iterable[str],
    *,
    stdin_handoff: bool = False,
    root_override: Path | None = None,
) -> AgentRun:
    allocation = load_active_allocation(settings, task_id, root_override=root_override)
    validate_allocation_for_run(settings, allocation)
    root = runs_root(settings, root_override)
    path = registry_path(settings, root_override)
    registry = reconcile_registry(settings, root_override=root_override)
    existing = latest_run(registry, task_id)
    if existing is not None and not existing.terminal:
        raise RunnerCollisionError(
            f"Task {task_id} already has non-terminal runner {existing.run_id} ({existing.status})"
        )

    command = expand_command(argv, allocation)
    run_id = uuid.uuid4().hex
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    result_path = run_dir / "result.json"
    stdout_path.touch()
    stderr_path.touch()
    now = _utc_now()

    wrapper_argv = [
        sys.executable,
        "-m",
        "engineering_graph.runner_child",
        "--run-id",
        run_id,
        "--result",
        str(result_path),
        "--stdout",
        str(stdout_path),
        "--stderr",
        str(stderr_path),
        "--argv-json",
        json.dumps(list(command)),
    ]
    if stdin_handoff:
        wrapper_argv.extend(["--stdin-file", allocation.handoff_path])

    process = subprocess.Popen(
        wrapper_argv,
        cwd=allocation.worktree_path,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    fingerprint = process_fingerprint(process.pid)
    try:
        process_group_id = os.getpgid(process.pid) if hasattr(os, "getpgid") else None
    except ProcessLookupError:
        process_group_id = None

    run = AgentRun(
        run_id=run_id,
        repository=allocation.repository,
        task_id=allocation.task_id,
        spec_id=allocation.spec_id,
        source_revision=allocation.source_revision,
        agent=allocation.agent,
        branch=allocation.branch,
        worktree_path=allocation.worktree_path,
        handoff_path=allocation.handoff_path,
        context_path=allocation.context_path,
        argv=command,
        stdin_handoff=stdin_handoff,
        pid=process.pid,
        process_fingerprint=fingerprint,
        process_group_id=process_group_id,
        status="running",
        exit_code=None,
        stop_requested=False,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        result_path=str(result_path),
        created_at=now,
        started_at=now,
        finished_at=None,
        updated_at=now,
    )
    updated = RunnerRegistry(registry.repository, registry.runs + (run,), registry.registry_version)
    _save_run_files(path, updated, run)
    return run


def _verified_for_signal(run: AgentRun) -> None:
    if run.pid is None:
        raise RunnerError("Runner process has no pid")
    if run.process_fingerprint is None:
        raise RunnerError("Runner process identity is not verifiable on this platform; refusing to signal")
    current = process_fingerprint(run.pid)
    if current is None:
        raise RunnerError("Runner process is not alive or its identity cannot be observed")
    if current != run.process_fingerprint:
        raise RunnerError("Runner process fingerprint mismatch; refusing to signal a potentially reused PID")


def _signal_run(run: AgentRun, sig: signal.Signals) -> None:
    if run.pid is None:
        raise RunnerError("Runner process has no pid")
    if run.process_group_id is not None and hasattr(os, "killpg"):
        os.killpg(run.process_group_id, sig)
    else:
        os.kill(run.pid, sig)


def stop_run(
    settings: GraphSettings,
    task_id: str,
    *,
    root_override: Path | None = None,
    timeout_seconds: float = 5.0,
    force: bool = False,
) -> AgentRun:
    path = registry_path(settings, root_override)
    registry = reconcile_registry(settings, root_override=root_override)
    run = latest_run(registry, task_id)
    if run is None:
        raise RunnerError(f"No runner history exists for task {task_id}")
    if run.terminal:
        return run

    _verified_for_signal(run)
    now = _utc_now()
    requested = replace(run, stop_requested=True, updated_at=now)
    registry = _replace_run(registry, requested)
    _save_run_files(path, registry, requested)
    _signal_run(requested, signal.SIGTERM)

    deadline = time.monotonic() + max(timeout_seconds, 0.0)
    while time.monotonic() < deadline:
        time.sleep(0.05)
        refreshed_registry = reconcile_registry(settings, root_override=root_override)
        refreshed = latest_run(refreshed_registry, task_id)
        if refreshed is not None and refreshed.terminal:
            return refreshed

    if not force:
        raise RunnerError(
            f"Runner {run.run_id} did not stop within {timeout_seconds}s; retry with --force for explicit escalation"
        )

    current_registry = reconcile_registry(settings, root_override=root_override)
    current = latest_run(current_registry, task_id)
    if current is None or current.terminal:
        return current or requested
    _verified_for_signal(current)
    _signal_run(current, signal.SIGKILL)

    deadline = time.monotonic() + max(timeout_seconds, 0.0)
    while time.monotonic() < deadline:
        time.sleep(0.05)
        refreshed_registry = reconcile_registry(settings, root_override=root_override)
        refreshed = latest_run(refreshed_registry, task_id)
        if refreshed is not None and refreshed.terminal:
            return refreshed
    raise RunnerError(f"Runner {run.run_id} remained alive after force escalation")


def status_runs(
    settings: GraphSettings,
    *,
    task_id: str | None = None,
    root_override: Path | None = None,
) -> tuple[AgentRun, ...]:
    registry = reconcile_registry(settings, root_override=root_override)
    values = registry.runs
    if task_id is not None:
        values = tuple(run for run in values if run.task_id == task_id)
    return tuple(sorted(values, key=lambda item: (item.created_at, item.run_id)))


def read_run_logs(
    settings: GraphSettings,
    task_id: str,
    *,
    stream: str = "stdout",
    max_bytes: int = 65536,
    root_override: Path | None = None,
) -> dict[str, str]:
    registry = reconcile_registry(settings, root_override=root_override)
    run = latest_run(registry, task_id)
    if run is None:
        raise RunnerError(f"No runner history exists for task {task_id}")
    if stream not in {"stdout", "stderr", "both"}:
        raise RunnerError(f"Unsupported runner log stream: {stream}")
    limit = max(1, min(max_bytes, 1024 * 1024))

    def tail(path: str) -> str:
        file_path = Path(path)
        if not file_path.is_file():
            return ""
        with file_path.open("rb") as handle:
            size = file_path.stat().st_size
            if size > limit:
                handle.seek(size - limit)
            return handle.read().decode("utf-8", errors="replace")

    payload: dict[str, str] = {}
    if stream in {"stdout", "both"}:
        payload["stdout"] = tail(run.stdout_path)
    if stream in {"stderr", "both"}:
        payload["stderr"] = tail(run.stderr_path)
    return payload
