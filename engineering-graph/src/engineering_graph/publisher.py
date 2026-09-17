from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Iterable
from urllib.parse import urlparse
import uuid

from .config import GraphSettings
from .execution import ExecutionAllocation
from .runner import execution_root, load_active_allocation, validate_allocation_for_run
from .validation import ValidationRecord, load_validation_record, workspace_identity

PUBLICATION_VERSION = "1"
PUBLICATION_STATUSES = frozenset({"started", "committed", "pushed", "pr_opened", "failed"})
PUBLICATION_PHASES = frozenset({"preflight", "commit", "push", "pr"})


class PublicationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PublicationRecord:
    publication_id: str
    repository: str
    task_id: str
    spec_id: str
    validation_id: str
    run_id: str
    source_revision: str
    workspace_revision: str
    workspace_fingerprint: str
    branch: str
    base_branch: str
    worktree_path: str
    commit_message: str
    pr_title: str
    pr_body: str
    status: str
    created_at: str
    updated_at: str
    last_successful_phase: str | None = None
    commit_sha: str | None = None
    pr_url: str | None = None
    failed_phase: str | None = None
    error: str | None = None
    finished_at: str | None = None
    publication_version: str = PUBLICATION_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "publicationVersion": self.publication_version,
            "publicationId": self.publication_id,
            "repository": self.repository,
            "taskId": self.task_id,
            "specId": self.spec_id,
            "validationId": self.validation_id,
            "runId": self.run_id,
            "sourceRevision": self.source_revision,
            "workspaceRevision": self.workspace_revision,
            "workspaceFingerprint": self.workspace_fingerprint,
            "branch": self.branch,
            "baseBranch": self.base_branch,
            "worktreePath": self.worktree_path,
            "commitMessage": self.commit_message,
            "prTitle": self.pr_title,
            "prBody": self.pr_body,
            "status": self.status,
            "lastSuccessfulPhase": self.last_successful_phase,
            "commitSha": self.commit_sha,
            "prUrl": self.pr_url,
            "failedPhase": self.failed_phase,
            "error": self.error,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "finishedAt": self.finished_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PublicationRecord":
        return cls(
            publication_id=str(raw.get("publicationId") or ""),
            repository=str(raw.get("repository") or ""),
            task_id=str(raw.get("taskId") or ""),
            spec_id=str(raw.get("specId") or ""),
            validation_id=str(raw.get("validationId") or ""),
            run_id=str(raw.get("runId") or ""),
            source_revision=str(raw.get("sourceRevision") or ""),
            workspace_revision=str(raw.get("workspaceRevision") or ""),
            workspace_fingerprint=str(raw.get("workspaceFingerprint") or ""),
            branch=str(raw.get("branch") or ""),
            base_branch=str(raw.get("baseBranch") or ""),
            worktree_path=str(raw.get("worktreePath") or ""),
            commit_message=str(raw.get("commitMessage") or ""),
            pr_title=str(raw.get("prTitle") or ""),
            pr_body=str(raw.get("prBody") or ""),
            status=str(raw.get("status") or ""),
            last_successful_phase=(str(raw["lastSuccessfulPhase"]) if raw.get("lastSuccessfulPhase") is not None else None),
            commit_sha=str(raw["commitSha"]) if raw.get("commitSha") is not None else None,
            pr_url=str(raw["prUrl"]) if raw.get("prUrl") is not None else None,
            failed_phase=str(raw["failedPhase"]) if raw.get("failedPhase") is not None else None,
            error=str(raw["error"]) if raw.get("error") is not None else None,
            created_at=str(raw.get("createdAt") or ""),
            updated_at=str(raw.get("updatedAt") or ""),
            finished_at=str(raw["finishedAt"]) if raw.get("finishedAt") is not None else None,
            publication_version=str(raw.get("publicationVersion") or ""),
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_publication_record(record: PublicationRecord) -> None:
    if record.publication_version != PUBLICATION_VERSION:
        raise PublicationError(f"Unsupported publication version: {record.publication_version}")
    required = {
        "publicationId": record.publication_id,
        "repository": record.repository,
        "taskId": record.task_id,
        "specId": record.spec_id,
        "validationId": record.validation_id,
        "runId": record.run_id,
        "sourceRevision": record.source_revision,
        "workspaceRevision": record.workspace_revision,
        "workspaceFingerprint": record.workspace_fingerprint,
        "branch": record.branch,
        "baseBranch": record.base_branch,
        "worktreePath": record.worktree_path,
        "commitMessage": record.commit_message,
        "prTitle": record.pr_title,
        "createdAt": record.created_at,
        "updatedAt": record.updated_at,
    }
    missing = [name for name, value in required.items() if not value.strip()]
    if missing:
        raise PublicationError(f"Publication record missing required fields: {', '.join(missing)}")
    if record.status not in PUBLICATION_STATUSES:
        raise PublicationError(f"Unsupported publication status: {record.status}")
    if record.last_successful_phase is not None and record.last_successful_phase not in PUBLICATION_PHASES:
        raise PublicationError(f"Unsupported successful publication phase: {record.last_successful_phase}")
    if record.failed_phase is not None and record.failed_phase not in PUBLICATION_PHASES:
        raise PublicationError(f"Unsupported failed publication phase: {record.failed_phase}")
    if record.status in {"committed", "pushed", "pr_opened"} and not record.commit_sha:
        raise PublicationError(f"Publication status {record.status} requires commitSha")
    if record.status == "pr_opened":
        if not record.pr_url:
            raise PublicationError("pr_opened publication requires prUrl")
        if record.failed_phase is not None or record.error is not None:
            raise PublicationError("pr_opened publication cannot retain failure fields")
    if record.status == "failed" and (record.failed_phase is None or not (record.error or "").strip()):
        raise PublicationError("Failed publication requires failedPhase and error")


def publication_root(settings: GraphSettings, override: Path | None = None) -> Path:
    return execution_root(settings, override) / "publication"


def records_root(settings: GraphSettings, override: Path | None = None) -> Path:
    return publication_root(settings, override) / "records"


def _record_path(settings: GraphSettings, publication_id: str, override: Path | None) -> Path:
    if not publication_id.strip() or "/" in publication_id or "\\" in publication_id:
        raise PublicationError("Invalid publication id")
    return records_root(settings, override) / f"{publication_id}.json"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def save_publication_record(settings: GraphSettings, record: PublicationRecord, *, root_override: Path | None = None) -> None:
    validate_publication_record(record)
    _atomic_json(_record_path(settings, record.publication_id, root_override), record.to_dict())


def load_publication_record(settings: GraphSettings, publication_id: str, *, root_override: Path | None = None) -> PublicationRecord:
    path = _record_path(settings, publication_id, root_override)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise PublicationError(f"Publication record not found: {publication_id}") from error
    except json.JSONDecodeError as error:
        raise PublicationError(f"Publication record is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise PublicationError("Publication record root must be a JSON object")
    record = PublicationRecord.from_dict(raw)
    validate_publication_record(record)
    return record


def list_publication_records(settings: GraphSettings, *, task_id: str | None = None, validation_id: str | None = None, root_override: Path | None = None) -> tuple[PublicationRecord, ...]:
    root = records_root(settings, root_override)
    if not root.is_dir():
        return ()
    records = tuple(load_publication_record(settings, path.stem, root_override=root_override) for path in root.glob("*.json"))
    filtered = tuple(record for record in records if (task_id is None or record.task_id == task_id) and (validation_id is None or record.validation_id == validation_id))
    return tuple(sorted(filtered, key=lambda item: (item.created_at, item.publication_id)))


def status_publications(settings: GraphSettings, *, task_id: str | None = None, validation_id: str | None = None, publication_id: str | None = None, root_override: Path | None = None) -> tuple[PublicationRecord, ...]:
    if publication_id is not None:
        record = load_publication_record(settings, publication_id, root_override=root_override)
        if task_id is not None and record.task_id != task_id:
            return ()
        if validation_id is not None and record.validation_id != validation_id:
            return ()
        return (record,)
    return list_publication_records(settings, task_id=task_id, validation_id=validation_id, root_override=root_override)


@dataclass(frozen=True, slots=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def _run_command(worktree: Path, argv: Iterable[str]) -> CommandResult:
    values = tuple(str(value) for value in argv)
    if not values:
        raise PublicationError("Publication command argv cannot be empty")
    completed = subprocess.run(list(values), cwd=worktree, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, shell=False, close_fds=True)
    return CommandResult(values, completed.returncode, completed.stdout, completed.stderr)


def _sanitize_error(value: str) -> str:
    text = value.strip()
    text = re.sub(r"https://[^/@\s]+@", "https://***@", text)
    text = re.sub(r"\b(?:gh[opsu]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,})\b", "***", text)
    return text[:4000]


def _checked(worktree: Path, argv: Iterable[str], *, label: str) -> CommandResult:
    result = _run_command(worktree, argv)
    if result.returncode != 0:
        detail = _sanitize_error(result.stderr or result.stdout or f"exit {result.returncode}")
        raise PublicationError(f"{label} failed: {detail}")
    return result


def _git(worktree: Path, *args: str, label: str | None = None) -> CommandResult:
    return _checked(worktree, ("git", *args), label=label or f"git {' '.join(args)}")


def _remote_repository(remote_url: str) -> str:
    value = remote_url.strip()
    if not value:
        raise PublicationError("origin remote URL is empty")
    scp = re.fullmatch(r"git@github\.com:([^/]+)/(.+)", value, flags=re.IGNORECASE)
    if scp:
        owner, repo = scp.group(1), scp.group(2)
    else:
        parsed = urlparse(value)
        if (parsed.hostname or "").lower() != "github.com":
            raise PublicationError("origin must use github.com for Git Publisher V8")
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 2:
            raise PublicationError("origin GitHub URL must identify exactly owner/repository")
        owner, repo = parts
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not owner or not repo:
        raise PublicationError("origin remote does not identify owner/repository")
    return f"{owner}/{repo}"


def _assert_origin_repository(settings: GraphSettings, worktree: Path) -> None:
    result = _git(worktree, "remote", "get-url", "origin", label="read origin remote")
    actual = _remote_repository(result.stdout)
    if actual.lower() != settings.repository_id.lower():
        raise PublicationError(f"origin repository mismatch: expected={settings.repository_id!r} actual={actual!r}")


def _assert_branch(worktree: Path, branch: str) -> None:
    check = _run_command(worktree, ("git", "check-ref-format", "--branch", branch))
    if check.returncode != 0:
        raise PublicationError(f"Invalid allocation branch: {branch!r}")
    current = _git(worktree, "rev-parse", "--abbrev-ref", "HEAD", label="read current branch").stdout.strip()
    if current != branch:
        raise PublicationError(f"Allocation branch mismatch: expected={branch!r} actual={current!r}")


def _assert_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise PublicationError(f"Required executable is unavailable: {name}")


def _assert_validation_matches_allocation(validation: ValidationRecord, allocation: ExecutionAllocation) -> None:
    if validation.status != "passed" or not validation.workspace_stable:
        raise PublicationError(f"Validation {validation.validation_id} is not passed/stable")
    mismatches: list[str] = []
    if validation.repository != allocation.repository:
        mismatches.append("repository")
    if validation.task_id != allocation.task_id:
        mismatches.append("taskId")
    if validation.spec_id != allocation.spec_id:
        mismatches.append("specId")
    if validation.source_revision != allocation.source_revision:
        mismatches.append("sourceRevision")
    if validation.branch != allocation.branch:
        mismatches.append("branch")
    if Path(validation.worktree_path).resolve() != Path(allocation.worktree_path).resolve():
        mismatches.append("worktreePath")
    if mismatches:
        raise PublicationError(f"Validation/allocation mismatch for {allocation.task_id}: {', '.join(mismatches)}")


def _assert_current_validated_workspace(worktree: Path, validation: ValidationRecord) -> None:
    revision, fingerprint = workspace_identity(worktree)
    if revision != validation.workspace_revision:
        raise PublicationError(f"Validated workspace revision is stale: validation={validation.workspace_revision} current={revision}")
    if fingerprint != validation.workspace_fingerprint_after:
        raise PublicationError("Validated workspace fingerprint is stale; re-run V7 before publication")


def _has_publishable_changes(worktree: Path) -> bool:
    result = _git(worktree, "status", "--porcelain=v1", "--untracked-files=all", label="inspect publishable changes")
    return bool(result.stdout.strip())


def _assert_no_existing_publication(settings: GraphSettings, validation_id: str, *, root_override: Path | None) -> None:
    existing = list_publication_records(settings, validation_id=validation_id, root_override=root_override)
    if not existing:
        return
    latest = existing[-1]
    if latest.status == "pr_opened":
        raise PublicationError(f"Validation {validation_id} was already published as {latest.pr_url}")
    raise PublicationError(f"Validation {validation_id} already has publication {latest.publication_id}; resume it instead")


def _preflight(settings: GraphSettings, task_id: str, validation_id: str, base_branch: str, *, root_override: Path | None) -> tuple[ExecutionAllocation, ValidationRecord, Path]:
    _assert_binary("git")
    _assert_binary("gh")
    allocation = load_active_allocation(settings, task_id, root_override=root_override)
    validate_allocation_for_run(settings, allocation)
    validation = load_validation_record(settings, validation_id, root_override=root_override)
    _assert_validation_matches_allocation(validation, allocation)
    worktree = Path(allocation.worktree_path).resolve()
    _assert_branch(worktree, allocation.branch)
    _assert_origin_repository(settings, worktree)
    base_check = _run_command(worktree, ("git", "check-ref-format", "--branch", base_branch))
    if base_check.returncode != 0:
        raise PublicationError(f"Invalid PR base branch: {base_branch!r}")
    if allocation.branch == base_branch:
        raise PublicationError("Publication branch and PR base branch must differ")
    _assert_current_validated_workspace(worktree, validation)
    if not _has_publishable_changes(worktree):
        raise PublicationError("Validated workspace has no publishable changes")
    _assert_no_existing_publication(settings, validation_id, root_override=root_override)
    return allocation, validation, worktree


def _save(settings: GraphSettings, record: PublicationRecord, *, root_override: Path | None) -> PublicationRecord:
    save_publication_record(settings, record, root_override=root_override)
    return record


def _failed(settings: GraphSettings, record: PublicationRecord, phase: str, error: Exception, *, root_override: Path | None) -> PublicationRecord:
    now = _utc_now()
    message = _sanitize_error(str(error)) or type(error).__name__
    failed = replace(record, status="failed", failed_phase=phase, error=message, updated_at=now, finished_at=now)
    return _save(settings, failed, root_override=root_override)


def _assert_committed_workspace(record: PublicationRecord) -> None:
    if not record.commit_sha:
        raise PublicationError("Publication has no commit SHA")
    worktree = Path(record.worktree_path)
    current = _git(worktree, "rev-parse", "HEAD", label="read publication commit").stdout.strip()
    if current != record.commit_sha:
        raise PublicationError(f"Publication commit drift: recorded={record.commit_sha} current={current}")
    parent = _git(worktree, "rev-parse", f"{record.commit_sha}^", label="read publication parent").stdout.strip()
    if parent != record.workspace_revision:
        raise PublicationError(f"Publication parent mismatch: expected={record.workspace_revision} actual={parent}")
    status = _git(worktree, "status", "--porcelain=v1", "--untracked-files=all", label="verify committed workspace cleanliness")
    if status.stdout.strip():
        raise PublicationError("Publication worktree is not clean at recorded commit")


def _stage_and_commit(settings: GraphSettings, record: PublicationRecord, *, root_override: Path | None) -> PublicationRecord:
    worktree = Path(record.worktree_path)
    try:
        _git(worktree, "add", "-A", "--", label="stage validated workspace")
        staged = _run_command(worktree, ("git", "diff", "--cached", "--quiet", "--exit-code"))
        if staged.returncode == 0:
            raise PublicationError("Validated workspace produced no staged changes")
        if staged.returncode != 1:
            raise PublicationError(f"Unable to inspect staged changes: {_sanitize_error(staged.stderr)}")
        unstaged = _run_command(worktree, ("git", "diff", "--quiet", "--exit-code"))
        if unstaged.returncode != 0:
            raise PublicationError("Workspace changed while publication was staging files")
        untracked = _git(worktree, "ls-files", "--others", "--exclude-standard", label="inspect untracked files after staging")
        if untracked.stdout.strip():
            raise PublicationError("Untracked files appeared while publication was staging files")
        head = _git(worktree, "rev-parse", "HEAD", label="read validated HEAD").stdout.strip()
        if head != record.workspace_revision:
            raise PublicationError(f"Workspace HEAD changed during publication: expected={record.workspace_revision} actual={head}")
        tree_sha = _git(worktree, "write-tree", label="write validated Git tree").stdout.strip()
        commit_sha = _git(worktree, "commit-tree", tree_sha, "-p", head, "-m", record.commit_message, label="create validated commit").stdout.strip()
        if not commit_sha:
            raise PublicationError("git commit-tree returned an empty commit SHA")
        _git(worktree, "update-ref", f"refs/heads/{record.branch}", commit_sha, head, label="advance publication branch")
        committed = replace(record, status="committed", last_successful_phase="commit", commit_sha=commit_sha, failed_phase=None, error=None, finished_at=None, updated_at=_utc_now())
        _save(settings, committed, root_override=root_override)
        _assert_committed_workspace(committed)
        return committed
    except Exception as error:
        current = record
        try:
            head_now = _git(worktree, "rev-parse", "HEAD", label="read failed commit HEAD").stdout.strip()
            if head_now == record.workspace_revision:
                _git(worktree, "reset", "--mixed", "HEAD", label="restore staging after failed commit")
            elif head_now:
                current = replace(current, commit_sha=head_now, last_successful_phase="commit")
        except Exception:
            pass
        return _failed(settings, current, "commit", error, root_override=root_override)


def _push(settings: GraphSettings, record: PublicationRecord, *, root_override: Path | None) -> PublicationRecord:
    worktree = Path(record.worktree_path)
    try:
        _assert_committed_workspace(record)
        _assert_origin_repository(settings, worktree)
        _git(worktree, "push", "--set-upstream", "origin", f"HEAD:refs/heads/{record.branch}", label="push validated publication branch")
        pushed = replace(record, status="pushed", last_successful_phase="push", failed_phase=None, error=None, finished_at=None, updated_at=_utc_now())
        return _save(settings, pushed, root_override=root_override)
    except Exception as error:
        return _failed(settings, record, "push", error, root_override=root_override)


def _existing_pr_url(record: PublicationRecord) -> str | None:
    result = _checked(Path(record.worktree_path), ("gh", "pr", "list", "--repo", record.repository, "--head", record.branch, "--base", record.base_branch, "--state", "open", "--json", "url", "--limit", "2"), label="inspect existing pull request")
    try:
        payload = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as error:
        raise PublicationError(f"gh pr list returned invalid JSON: {error}") from error
    if not isinstance(payload, list):
        raise PublicationError("gh pr list returned an invalid payload")
    urls = [str(item.get("url") or "") for item in payload if isinstance(item, dict) and str(item.get("url") or "").strip()]
    if len(urls) > 1:
        raise PublicationError(f"Multiple open pull requests already use branch {record.branch}")
    return urls[0] if urls else None


def _create_pr(record: PublicationRecord) -> str:
    existing = _existing_pr_url(record)
    if existing:
        return existing
    result = _checked(Path(record.worktree_path), ("gh", "pr", "create", "--repo", record.repository, "--base", record.base_branch, "--head", record.branch, "--title", record.pr_title, "--body", record.pr_body), label="create GitHub pull request")
    candidates = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith(("https://", "http://"))]
    if not candidates:
        raise PublicationError("gh pr create did not return a pull request URL")
    url = candidates[-1]
    if not re.match(r"^https://github\.com/[^/]+/[^/]+/pull/\d+(?:\?.*)?$", url):
        raise PublicationError(f"Unexpected pull request URL returned by gh: {url}")
    return url


def _open_pr(settings: GraphSettings, record: PublicationRecord, *, root_override: Path | None) -> PublicationRecord:
    try:
        _assert_committed_workspace(record)
        url = _create_pr(record)
        now = _utc_now()
        opened = replace(record, status="pr_opened", last_successful_phase="pr", pr_url=url, failed_phase=None, error=None, updated_at=now, finished_at=now)
        return _save(settings, opened, root_override=root_override)
    except Exception as error:
        return _failed(settings, record, "pr", error, root_override=root_override)


def run_publication(settings: GraphSettings, task_id: str, validation_id: str, *, commit_message: str, pr_title: str, pr_body: str = "", base_branch: str = "master", root_override: Path | None = None) -> PublicationRecord:
    if not commit_message.strip():
        raise PublicationError("Commit message is required")
    if not pr_title.strip():
        raise PublicationError("PR title is required")
    allocation, validation, worktree = _preflight(settings, task_id, validation_id, base_branch, root_override=root_override)
    now = _utc_now()
    record = PublicationRecord(
        publication_id=uuid.uuid4().hex,
        repository=allocation.repository,
        task_id=allocation.task_id,
        spec_id=allocation.spec_id,
        validation_id=validation.validation_id,
        run_id=validation.run_id,
        source_revision=allocation.source_revision,
        workspace_revision=validation.workspace_revision,
        workspace_fingerprint=validation.workspace_fingerprint_after,
        branch=allocation.branch,
        base_branch=base_branch,
        worktree_path=str(worktree),
        commit_message=commit_message,
        pr_title=pr_title,
        pr_body=pr_body,
        status="started",
        last_successful_phase="preflight",
        created_at=now,
        updated_at=now,
    )
    _save(settings, record, root_override=root_override)
    committed = _stage_and_commit(settings, record, root_override=root_override)
    if committed.status == "failed":
        return committed
    pushed = _push(settings, committed, root_override=root_override)
    if pushed.status == "failed":
        return pushed
    return _open_pr(settings, pushed, root_override=root_override)


def _assert_resume_identity(settings: GraphSettings, record: PublicationRecord, *, root_override: Path | None) -> tuple[ExecutionAllocation, ValidationRecord]:
    allocation = load_active_allocation(settings, record.task_id, root_override=root_override)
    validate_allocation_for_run(settings, allocation)
    validation = load_validation_record(settings, record.validation_id, root_override=root_override)
    _assert_validation_matches_allocation(validation, allocation)
    mismatches: list[str] = []
    if record.repository != allocation.repository:
        mismatches.append("repository")
    if record.spec_id != allocation.spec_id:
        mismatches.append("specId")
    if record.source_revision != allocation.source_revision:
        mismatches.append("sourceRevision")
    if record.branch != allocation.branch:
        mismatches.append("branch")
    if Path(record.worktree_path).resolve() != Path(allocation.worktree_path).resolve():
        mismatches.append("worktreePath")
    if record.run_id != validation.run_id:
        mismatches.append("runId")
    if record.workspace_revision != validation.workspace_revision:
        mismatches.append("workspaceRevision")
    if record.workspace_fingerprint != validation.workspace_fingerprint_after:
        mismatches.append("workspaceFingerprint")
    if mismatches:
        raise PublicationError(f"Publication resume identity drift: {', '.join(mismatches)}")
    _assert_branch(Path(record.worktree_path), record.branch)
    _assert_origin_repository(settings, Path(record.worktree_path))
    return allocation, validation


def resume_publication(settings: GraphSettings, publication_id: str, *, root_override: Path | None = None) -> PublicationRecord:
    _assert_binary("git")
    _assert_binary("gh")
    record = load_publication_record(settings, publication_id, root_override=root_override)
    if record.status == "pr_opened":
        return record
    _assert_resume_identity(settings, record, root_override=root_override)
    if record.commit_sha is None:
        validation = load_validation_record(settings, record.validation_id, root_override=root_override)
        _assert_current_validated_workspace(Path(record.worktree_path), validation)
        if not _has_publishable_changes(Path(record.worktree_path)):
            raise PublicationError("Validated workspace has no publishable changes to resume")
        reset = replace(record, status="started", last_successful_phase="preflight", failed_phase=None, error=None, finished_at=None, updated_at=_utc_now())
        _save(settings, reset, root_override=root_override)
        committed = _stage_and_commit(settings, reset, root_override=root_override)
        if committed.status == "failed":
            return committed
        record = committed
    else:
        _assert_committed_workspace(record)
        if record.last_successful_phase not in {"commit", "push", "pr"}:
            record = replace(record, last_successful_phase="commit", status="committed", failed_phase=None, error=None, finished_at=None, updated_at=_utc_now())
            _save(settings, record, root_override=root_override)
    if record.last_successful_phase == "commit" or record.status == "committed":
        pushed = _push(settings, record, root_override=root_override)
        if pushed.status == "failed":
            return pushed
        record = pushed
    if record.last_successful_phase == "push" or record.status == "pushed":
        return _open_pr(settings, record, root_override=root_override)
    if record.last_successful_phase == "pr" and record.pr_url:
        opened = replace(record, status="pr_opened", failed_phase=None, error=None, finished_at=record.finished_at or _utc_now(), updated_at=_utc_now())
        return _save(settings, opened, root_override=root_override)
    raise PublicationError(f"Publication {publication_id} cannot be resumed from state {record.status}/{record.last_successful_phase}")
