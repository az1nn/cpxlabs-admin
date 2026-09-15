from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
from typing import Any
import uuid

from .config import GraphSettings
from .execution import ExecutionAllocation
from .runner import (
    AgentRun,
    execution_root,
    latest_run,
    load_active_allocation,
    reconcile_registry,
    validate_allocation_for_run,
)
from .supervisor import SupervisorJob, SupervisorTask, status_supervisor_jobs

VALIDATION_VERSION = "1"
VALIDATION_STATUSES = frozenset({"passed", "failed"})
COMMAND_STATUSES = frozenset({"passed", "failed"})


class ValidationError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class ValidationCommandResult:
    index: int
    command: str
    argv: tuple[str, ...]
    status: str
    exit_code: int | None
    stdout_path: str
    stderr_path: str
    started_at: str
    finished_at: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "command": self.command,
            "argv": list(self.argv),
            "status": self.status,
            "exitCode": self.exit_code,
            "stdoutPath": self.stdout_path,
            "stderrPath": self.stderr_path,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ValidationCommandResult":
        return cls(
            index=int(raw.get("index") or 0),
            command=str(raw.get("command") or ""),
            argv=tuple(str(value) for value in (raw.get("argv") or [])),
            status=str(raw.get("status") or ""),
            exit_code=int(raw["exitCode"]) if raw.get("exitCode") is not None else None,
            stdout_path=str(raw.get("stdoutPath") or ""),
            stderr_path=str(raw.get("stderrPath") or ""),
            started_at=str(raw.get("startedAt") or ""),
            finished_at=str(raw.get("finishedAt") or ""),
            error=str(raw["error"]) if raw.get("error") is not None else None,
        )


@dataclass(frozen=True, slots=True)
class ValidationRecord:
    validation_id: str
    repository: str
    task_id: str
    spec_id: str
    source_revision: str
    run_id: str
    branch: str
    worktree_path: str
    workspace_revision: str
    workspace_fingerprint_before: str
    workspace_fingerprint_after: str
    workspace_stable: bool
    status: str
    commands: tuple[ValidationCommandResult, ...]
    created_at: str
    finished_at: str
    validation_version: str = VALIDATION_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "validationVersion": self.validation_version,
            "validationId": self.validation_id,
            "repository": self.repository,
            "taskId": self.task_id,
            "specId": self.spec_id,
            "sourceRevision": self.source_revision,
            "runId": self.run_id,
            "branch": self.branch,
            "worktreePath": self.worktree_path,
            "workspaceRevision": self.workspace_revision,
            "workspaceFingerprintBefore": self.workspace_fingerprint_before,
            "workspaceFingerprintAfter": self.workspace_fingerprint_after,
            "workspaceStable": self.workspace_stable,
            "status": self.status,
            "commands": [result.to_dict() for result in self.commands],
            "createdAt": self.created_at,
            "finishedAt": self.finished_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ValidationRecord":
        return cls(
            validation_id=str(raw.get("validationId") or ""),
            repository=str(raw.get("repository") or ""),
            task_id=str(raw.get("taskId") or ""),
            spec_id=str(raw.get("specId") or ""),
            source_revision=str(raw.get("sourceRevision") or ""),
            run_id=str(raw.get("runId") or ""),
            branch=str(raw.get("branch") or ""),
            worktree_path=str(raw.get("worktreePath") or ""),
            workspace_revision=str(raw.get("workspaceRevision") or ""),
            workspace_fingerprint_before=str(raw.get("workspaceFingerprintBefore") or ""),
            workspace_fingerprint_after=str(raw.get("workspaceFingerprintAfter") or ""),
            workspace_stable=bool(raw.get("workspaceStable", False)),
            status=str(raw.get("status") or ""),
            commands=tuple(
                ValidationCommandResult.from_dict(item)
                for item in (raw.get("commands") or [])
                if isinstance(item, dict)
            ),
            created_at=str(raw.get("createdAt") or ""),
            finished_at=str(raw.get("finishedAt") or ""),
            validation_version=str(raw.get("validationVersion") or ""),
        )


def validate_command_result(result: ValidationCommandResult) -> None:
    if result.index < 1:
        raise ValidationError("Validation command index must be positive")
    if not result.command.strip() or not result.argv:
        raise ValidationError("Validation command and argv are required")
    if result.status not in COMMAND_STATUSES:
        raise ValidationError(f"Unsupported validation command status: {result.status}")
    if not result.stdout_path or not result.stderr_path or not result.started_at or not result.finished_at:
        raise ValidationError("Validation command log paths and timestamps are required")
    if result.status == "passed" and result.exit_code != 0:
        raise ValidationError("Passed validation command must have exit code 0")
    if result.status == "failed" and result.exit_code == 0:
        raise ValidationError("Failed validation command cannot have exit code 0")


def validate_record(record: ValidationRecord) -> None:
    if record.validation_version != VALIDATION_VERSION:
        raise ValidationError(f"Unsupported validation version: {record.validation_version}")
    required = {
        "validationId": record.validation_id,
        "repository": record.repository,
        "taskId": record.task_id,
        "specId": record.spec_id,
        "sourceRevision": record.source_revision,
        "runId": record.run_id,
        "branch": record.branch,
        "worktreePath": record.worktree_path,
        "workspaceRevision": record.workspace_revision,
        "workspaceFingerprintBefore": record.workspace_fingerprint_before,
        "workspaceFingerprintAfter": record.workspace_fingerprint_after,
        "createdAt": record.created_at,
        "finishedAt": record.finished_at,
    }
    missing = [name for name, value in required.items() if not value.strip()]
    if missing:
        raise ValidationError(f"Validation record missing required fields: {', '.join(missing)}")
    if record.status not in VALIDATION_STATUSES:
        raise ValidationError(f"Unsupported validation status: {record.status}")
    if not record.commands:
        raise ValidationError("Validation record must contain at least one command result")
    expected_indexes = tuple(range(1, len(record.commands) + 1))
    if tuple(result.index for result in record.commands) != expected_indexes:
        raise ValidationError("Validation command indexes must be contiguous starting at 1")
    for result in record.commands:
        validate_command_result(result)
    all_passed = all(result.status == "passed" for result in record.commands)
    if record.status == "passed" and (not all_passed or not record.workspace_stable):
        raise ValidationError("Passed validation requires all commands to pass and a stable workspace")


def validation_root(settings: GraphSettings, override: Path | None = None) -> Path:
    return execution_root(settings, override) / "validation"


def records_root(settings: GraphSettings, override: Path | None = None) -> Path:
    return validation_root(settings, override) / "records"


def _record_path(settings: GraphSettings, validation_id: str, override: Path | None) -> Path:
    if not validation_id.strip() or "/" in validation_id or "\\" in validation_id:
        raise ValidationError("Invalid validation id")
    return records_root(settings, override) / f"{validation_id}.json"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def save_validation_record(
    settings: GraphSettings,
    record: ValidationRecord,
    *,
    root_override: Path | None = None,
) -> None:
    validate_record(record)
    _atomic_json(_record_path(settings, record.validation_id, root_override), record.to_dict())


def load_validation_record(
    settings: GraphSettings,
    validation_id: str,
    *,
    root_override: Path | None = None,
) -> ValidationRecord:
    path = _record_path(settings, validation_id, root_override)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValidationError(f"Validation record not found: {validation_id}") from error
    except json.JSONDecodeError as error:
        raise ValidationError(f"Validation record is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise ValidationError("Validation record root must be a JSON object")
    record = ValidationRecord.from_dict(raw)
    validate_record(record)
    return record


def list_validation_records(
    settings: GraphSettings,
    *,
    task_id: str | None = None,
    root_override: Path | None = None,
) -> tuple[ValidationRecord, ...]:
    root = records_root(settings, root_override)
    if not root.is_dir():
        return ()
    records = tuple(load_validation_record(settings, path.stem, root_override=root_override) for path in root.glob("*.json"))
    filtered = tuple(record for record in records if task_id is None or record.task_id == task_id)
    return tuple(sorted(filtered, key=lambda item: (item.created_at, item.validation_id)))


def status_validations(
    settings: GraphSettings,
    *,
    task_id: str | None = None,
    validation_id: str | None = None,
    root_override: Path | None = None,
) -> tuple[ValidationRecord, ...]:
    if validation_id is not None:
        record = load_validation_record(settings, validation_id, root_override=root_override)
        if task_id is not None and record.task_id != task_id:
            return ()
        return (record,)
    return list_validation_records(settings, task_id=task_id, root_override=root_override)


def _git_output(worktree: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=worktree,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValidationError(f"Git workspace inspection failed ({' '.join(args)}): {message}")
    return result.stdout


def workspace_identity(worktree: Path) -> tuple[str, str]:
    revision = _git_output(worktree, "rev-parse", "HEAD").decode("utf-8").strip()
    if not revision:
        raise ValidationError("Allocated worktree has no Git HEAD")
    digest = hashlib.sha256()
    digest.update(b"workspace-v1\0")
    digest.update(revision.encode("ascii"))
    digest.update(b"\0tracked\0")
    digest.update(_git_output(worktree, "diff", "--binary", "--no-ext-diff", "--no-textconv", "HEAD", "--"))
    untracked_raw = _git_output(worktree, "ls-files", "--others", "--exclude-standard", "-z")
    untracked = sorted(path for path in untracked_raw.split(b"\0") if path)
    digest.update(b"\0untracked\0")
    for raw_path in untracked:
        relative = raw_path.decode("utf-8", errors="surrogateescape")
        path = worktree / relative
        digest.update(raw_path)
        digest.update(b"\0")
        if path.is_symlink():
            digest.update(b"symlink\0")
            digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
        elif path.is_file():
            digest.update(b"file\0")
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        else:
            digest.update(b"other\0")
        digest.update(b"\0")
    return revision, digest.hexdigest()


def _assert_run_matches_allocation(run: AgentRun, allocation: ExecutionAllocation) -> None:
    mismatches: list[str] = []
    if run.repository != allocation.repository:
        mismatches.append("repository")
    if run.task_id != allocation.task_id:
        mismatches.append("taskId")
    if run.spec_id != allocation.spec_id:
        mismatches.append("specId")
    if run.source_revision != allocation.source_revision:
        mismatches.append("sourceRevision")
    if run.branch != allocation.branch:
        mismatches.append("branch")
    if Path(run.worktree_path).resolve() != Path(allocation.worktree_path).resolve():
        mismatches.append("worktreePath")
    if mismatches:
        raise ValidationError(
            f"Latest V5 run does not match active allocation for {allocation.task_id}: {', '.join(mismatches)}"
        )


def _find_task(job: SupervisorJob, task_id: str) -> SupervisorTask | None:
    return next((task for task in job.tasks if task.task_id == task_id), None)


def _assert_supervisor_ownership(
    settings: GraphSettings,
    task_id: str,
    run: AgentRun,
    *,
    root_override: Path | None,
) -> None:
    jobs = status_supervisor_jobs(settings, root_override=root_override)
    active_claims: list[tuple[SupervisorJob, SupervisorTask]] = []
    exact_owners: list[tuple[SupervisorJob, SupervisorTask]] = []
    for job in jobs:
        task = _find_task(job, task_id)
        if task is None:
            continue
        if job.status == "active":
            active_claims.append((job, task))
        if run.run_id in task.run_ids:
            exact_owners.append((job, task))

    if len(active_claims) > 1:
        raise ValidationError(f"Multiple active supervisors claim task {task_id}")
    if active_claims:
        job, task = active_claims[0]
        owned = task.run_ids[-1] if task.run_ids else None
        if owned != run.run_id or task.status != "succeeded":
            raise ValidationError(
                f"Supervisor ownership mismatch for {task_id}: job={job.job_id} "
                f"owned={owned or '-'} latest={run.run_id} state={task.status}"
            )

    if exact_owners:
        job, task = sorted(exact_owners, key=lambda item: (item[0].created_at, item[0].job_id))[-1]
        owned = task.run_ids[-1] if task.run_ids else None
        if owned != run.run_id or task.status != "succeeded":
            raise ValidationError(
                f"Supervisor evidence is not successful for {task_id}: job={job.job_id} state={task.status}"
            )


def _prepare_commands(commands: tuple[str, ...]) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if not commands:
        raise ValidationError("Active allocation has no frozen validation commands")
    prepared: list[tuple[str, tuple[str, ...]]] = []
    for command in commands:
        try:
            argv = tuple(shlex.split(command, posix=True))
        except ValueError as error:
            raise ValidationError(f"Invalid frozen validation command {command!r}: {error}") from error
        if not argv:
            raise ValidationError("Frozen validation command cannot be empty")
        prepared.append((command, argv))
    return tuple(prepared)


def run_validation(
    settings: GraphSettings,
    task_id: str,
    *,
    root_override: Path | None = None,
) -> ValidationRecord:
    allocation = load_active_allocation(settings, task_id, root_override=root_override)
    validate_allocation_for_run(settings, allocation)
    prepared = _prepare_commands(allocation.validation_commands)

    registry = reconcile_registry(settings, root_override=root_override)
    run = latest_run(registry, task_id)
    if run is None:
        raise ValidationError(f"Task {task_id} has no V5 run to validate")
    if run.status != "succeeded":
        raise ValidationError(
            f"Latest V5 run for {task_id} must be succeeded before validation: {run.status}"
        )
    _assert_run_matches_allocation(run, allocation)
    _assert_supervisor_ownership(settings, task_id, run, root_override=root_override)

    worktree = Path(allocation.worktree_path).resolve()
    workspace_revision, fingerprint_before = workspace_identity(worktree)
    validation_id = uuid.uuid4().hex
    run_dir = validation_root(settings, root_override) / "runs" / validation_id
    run_dir.mkdir(parents=True, exist_ok=False)
    created_at = _utc_now()
    results: list[ValidationCommandResult] = []

    for index, (command, argv) in enumerate(prepared, start=1):
        stdout_path = run_dir / f"command-{index:03d}.stdout.log"
        stderr_path = run_dir / f"command-{index:03d}.stderr.log"
        started_at = _utc_now()
        exit_code: int | None = None
        error_text: str | None = None
        with stdout_path.open("wb") as stdout_handle, stderr_path.open("wb") as stderr_handle:
            try:
                completed = subprocess.run(
                    list(argv),
                    cwd=worktree,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    check=False,
                    shell=False,
                    close_fds=True,
                )
                exit_code = completed.returncode
            except OSError as error:
                error_text = f"{type(error).__name__}: {error}"
                stderr_handle.write((error_text + "\n").encode("utf-8", errors="replace"))
        finished_at = _utc_now()
        status = "passed" if exit_code == 0 and error_text is None else "failed"
        results.append(
            ValidationCommandResult(
                index=index,
                command=command,
                argv=argv,
                status=status,
                exit_code=exit_code,
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
                started_at=started_at,
                finished_at=finished_at,
                error=error_text,
            )
        )
        if status == "failed":
            break

    final_revision, fingerprint_after = workspace_identity(worktree)
    workspace_stable = (
        workspace_revision == final_revision and fingerprint_before == fingerprint_after
    )
    all_commands_passed = len(results) == len(prepared) and all(
        result.status == "passed" for result in results
    )
    status = "passed" if all_commands_passed and workspace_stable else "failed"
    record = ValidationRecord(
        validation_id=validation_id,
        repository=allocation.repository,
        task_id=allocation.task_id,
        spec_id=allocation.spec_id,
        source_revision=allocation.source_revision,
        run_id=run.run_id,
        branch=allocation.branch,
        worktree_path=str(worktree),
        workspace_revision=final_revision,
        workspace_fingerprint_before=fingerprint_before,
        workspace_fingerprint_after=fingerprint_after,
        workspace_stable=workspace_stable,
        status=status,
        commands=tuple(results),
        created_at=created_at,
        finished_at=_utc_now(),
    )
    save_validation_record(settings, record, root_override=root_override)
    return record
