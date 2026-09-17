from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable

from .config import GraphSettings
from .execution import ExecutionAllocation
from .leases import active_lease, load_registry, release_lease
from .publisher import PublicationRecord, load_publication_record
from .runner import execution_root
from .worktrees import find_worktree, is_worktree_dirty, list_worktrees, remove_worktree

RECEIPT_VERSION = "1"
RECEIPT_STATUSES = frozenset({"reconciled", "blocked", "finalized"})


class PostPublicationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PostPublicationReceipt:
    receipt_id: str
    repository: str
    publication_id: str
    validation_id: str
    task_id: str
    spec_id: str
    branch: str
    base_branch: str
    worktree_path: str
    pr_url: str
    pr_number: int
    merge_commit_sha: str
    base_revision: str
    canonical_task_path: str
    canonical_task_completed: bool
    lease_released: bool
    worktree_removed: bool
    status: str
    created_at: str
    updated_at: str
    block_reason: str | None = None
    finished_at: str | None = None
    receipt_version: str = RECEIPT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "receiptVersion": self.receipt_version,
            "receiptId": self.receipt_id,
            "repository": self.repository,
            "publicationId": self.publication_id,
            "validationId": self.validation_id,
            "taskId": self.task_id,
            "specId": self.spec_id,
            "branch": self.branch,
            "baseBranch": self.base_branch,
            "worktreePath": self.worktree_path,
            "prUrl": self.pr_url,
            "prNumber": self.pr_number,
            "mergeCommitSha": self.merge_commit_sha,
            "baseRevision": self.base_revision,
            "canonicalTaskPath": self.canonical_task_path,
            "canonicalTaskCompleted": self.canonical_task_completed,
            "leaseReleased": self.lease_released,
            "worktreeRemoved": self.worktree_removed,
            "status": self.status,
            "blockReason": self.block_reason,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "finishedAt": self.finished_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PostPublicationReceipt":
        return cls(
            receipt_id=str(raw.get("receiptId") or ""),
            repository=str(raw.get("repository") or ""),
            publication_id=str(raw.get("publicationId") or ""),
            validation_id=str(raw.get("validationId") or ""),
            task_id=str(raw.get("taskId") or ""),
            spec_id=str(raw.get("specId") or ""),
            branch=str(raw.get("branch") or ""),
            base_branch=str(raw.get("baseBranch") or ""),
            worktree_path=str(raw.get("worktreePath") or ""),
            pr_url=str(raw.get("prUrl") or ""),
            pr_number=int(raw.get("prNumber") or 0),
            merge_commit_sha=str(raw.get("mergeCommitSha") or ""),
            base_revision=str(raw.get("baseRevision") or ""),
            canonical_task_path=str(raw.get("canonicalTaskPath") or ""),
            canonical_task_completed=bool(raw.get("canonicalTaskCompleted", False)),
            lease_released=bool(raw.get("leaseReleased", False)),
            worktree_removed=bool(raw.get("worktreeRemoved", False)),
            status=str(raw.get("status") or ""),
            block_reason=str(raw["blockReason"]) if raw.get("blockReason") is not None else None,
            created_at=str(raw.get("createdAt") or ""),
            updated_at=str(raw.get("updatedAt") or ""),
            finished_at=str(raw["finishedAt"]) if raw.get("finishedAt") is not None else None,
            receipt_version=str(raw.get("receiptVersion") or ""),
        )


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    repository: str
    publication_id: str
    validation_id: str
    task_id: str
    spec_id: str
    branch: str
    base_branch: str
    worktree_path: str
    pr_url: str
    pr_number: int
    pr_merged: bool
    merge_commit_sha: str | None
    base_revision: str | None
    merge_reachable: bool
    canonical_task_path: str | None
    canonical_task_completed: bool
    lease_active: bool
    worktree_registered: bool
    worktree_dirty: bool | None
    already_finalized: bool
    finalizable: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "publicationId": self.publication_id,
            "validationId": self.validation_id,
            "taskId": self.task_id,
            "specId": self.spec_id,
            "branch": self.branch,
            "baseBranch": self.base_branch,
            "worktreePath": self.worktree_path,
            "prUrl": self.pr_url,
            "prNumber": self.pr_number,
            "prMerged": self.pr_merged,
            "mergeCommitSha": self.merge_commit_sha,
            "baseRevision": self.base_revision,
            "mergeReachable": self.merge_reachable,
            "canonicalTaskPath": self.canonical_task_path,
            "canonicalTaskCompleted": self.canonical_task_completed,
            "leaseActive": self.lease_active,
            "worktreeRegistered": self.worktree_registered,
            "worktreeDirty": self.worktree_dirty,
            "alreadyFinalized": self.already_finalized,
            "finalizable": self.finalizable,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True, slots=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def post_publication_root(settings: GraphSettings, root_override: Path | None = None) -> Path:
    return execution_root(settings, root_override) / "post-publication"


def receipts_root(settings: GraphSettings, root_override: Path | None = None) -> Path:
    return post_publication_root(settings, root_override) / "receipts"


def _receipt_path(settings: GraphSettings, publication_id: str, root_override: Path | None) -> Path:
    if not publication_id.strip() or "/" in publication_id or "\\" in publication_id:
        raise PostPublicationError("Invalid publication id")
    return receipts_root(settings, root_override) / f"{publication_id}.json"


def validate_receipt(receipt: PostPublicationReceipt) -> None:
    if receipt.receipt_version != RECEIPT_VERSION:
        raise PostPublicationError(f"Unsupported receipt version: {receipt.receipt_version}")
    required = {
        "receiptId": receipt.receipt_id,
        "repository": receipt.repository,
        "publicationId": receipt.publication_id,
        "validationId": receipt.validation_id,
        "taskId": receipt.task_id,
        "specId": receipt.spec_id,
        "branch": receipt.branch,
        "baseBranch": receipt.base_branch,
        "worktreePath": receipt.worktree_path,
        "prUrl": receipt.pr_url,
        "mergeCommitSha": receipt.merge_commit_sha,
        "baseRevision": receipt.base_revision,
        "canonicalTaskPath": receipt.canonical_task_path,
        "createdAt": receipt.created_at,
        "updatedAt": receipt.updated_at,
    }
    missing = [name for name, value in required.items() if not str(value).strip()]
    if missing:
        raise PostPublicationError(f"Post-publication receipt missing required fields: {', '.join(missing)}")
    if receipt.pr_number <= 0:
        raise PostPublicationError("Post-publication receipt requires positive prNumber")
    if receipt.status not in RECEIPT_STATUSES:
        raise PostPublicationError(f"Unsupported post-publication receipt status: {receipt.status}")
    if receipt.status == "finalized" and not receipt.lease_released:
        raise PostPublicationError("Finalized post-publication receipt requires leaseReleased=true")
    if receipt.status == "blocked" and not (receipt.block_reason or "").strip():
        raise PostPublicationError("Blocked post-publication receipt requires blockReason")


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def save_receipt(settings: GraphSettings, receipt: PostPublicationReceipt, *, root_override: Path | None = None) -> None:
    validate_receipt(receipt)
    _atomic_json(_receipt_path(settings, receipt.publication_id, root_override), receipt.to_dict())


def load_receipt(
    settings: GraphSettings,
    publication_id: str,
    *,
    root_override: Path | None = None,
    required: bool = True,
) -> PostPublicationReceipt | None:
    path = _receipt_path(settings, publication_id, root_override)
    if not path.is_file():
        if required:
            raise PostPublicationError(f"Post-publication receipt not found: {publication_id}")
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise PostPublicationError(f"Post-publication receipt is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise PostPublicationError("Post-publication receipt root must be a JSON object")
    receipt = PostPublicationReceipt.from_dict(raw)
    validate_receipt(receipt)
    return receipt


def _run_command(cwd: Path, argv: Iterable[str]) -> CommandResult:
    values = tuple(str(value) for value in argv)
    if not values:
        raise PostPublicationError("Post-publication command argv cannot be empty")
    completed = subprocess.run(
        list(values),
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        shell=False,
        close_fds=True,
    )
    return CommandResult(values, completed.returncode, completed.stdout, completed.stderr)


def _checked(cwd: Path, argv: Iterable[str], *, label: str) -> CommandResult:
    result = _run_command(cwd, argv)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or f"exit {result.returncode}").strip()[:4000]
        raise PostPublicationError(f"{label} failed: {detail}")
    return result


def _assert_publication(record: PublicationRecord, settings: GraphSettings) -> None:
    if record.repository != settings.repository_id:
        raise PostPublicationError(
            f"Publication repository mismatch: expected={settings.repository_id!r} actual={record.repository!r}"
        )
    if record.status != "pr_opened" or not record.pr_url or not record.commit_sha:
        raise PostPublicationError("Post-publication reconciliation requires a terminal pr_opened V8 publication")


def _inspect_pr(settings: GraphSettings, record: PublicationRecord) -> dict[str, Any]:
    result = _checked(
        settings.repo_root,
        (
            "gh",
            "pr",
            "view",
            record.pr_url,
            "--json",
            "number,state,mergedAt,mergeCommit,url,baseRefName,headRefName",
        ),
        label="inspect GitHub pull request",
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise PostPublicationError(f"GitHub PR response is not valid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise PostPublicationError("GitHub PR response root must be a JSON object")
    if str(payload.get("url") or "") != record.pr_url:
        raise PostPublicationError("GitHub PR URL does not match publication record")
    if str(payload.get("baseRefName") or "") != record.base_branch:
        raise PostPublicationError("GitHub PR base branch does not match publication record")
    if str(payload.get("headRefName") or "") != record.branch:
        raise PostPublicationError("GitHub PR head branch does not match publication record")
    return payload


def _refresh_base(settings: GraphSettings, base_branch: str) -> tuple[str, str]:
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", base_branch) or base_branch.startswith("-"):
        raise PostPublicationError(f"Invalid base branch: {base_branch!r}")
    remote_ref = f"refs/remotes/origin/{base_branch}"
    refspec = f"refs/heads/{base_branch}:{remote_ref}"
    _checked(settings.repo_root, ("git", "fetch", "--no-tags", "origin", refspec), label="refresh base branch")
    revision = _checked(settings.repo_root, ("git", "rev-parse", remote_ref), label="resolve refreshed base").stdout.strip()
    if not revision:
        raise PostPublicationError("Unable to resolve refreshed base revision")
    return remote_ref, revision


def _merge_reachable(settings: GraphSettings, merge_sha: str, base_ref: str) -> bool:
    result = _run_command(settings.repo_root, ("git", "merge-base", "--is-ancestor", merge_sha, base_ref))
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    detail = (result.stderr or result.stdout or f"exit {result.returncode}").strip()
    raise PostPublicationError(f"verify merge reachability failed: {detail}")


def _task_path(settings: GraphSettings, spec_id: str) -> str:
    match = re.fullmatch(r"SPEC-(\d{3})-[A-Z0-9-]+", spec_id)
    if not match:
        raise PostPublicationError(f"Unsupported Spec canonical ID for Task lookup: {spec_id!r}")
    prefix = f"{match.group(1)}-"
    specs_root = settings.repo_root / "specs"
    candidates = sorted(path for path in specs_root.iterdir() if path.is_dir() and path.name.startswith(prefix))
    if len(candidates) != 1:
        raise PostPublicationError(
            f"Expected exactly one Spec directory for {spec_id}; found {[path.name for path in candidates]}"
        )
    return f"specs/{candidates[0].name}/{settings.tasks_name}"


def _canonical_task_completed(
    settings: GraphSettings,
    *,
    base_ref: str,
    spec_id: str,
    task_id: str,
) -> tuple[str, bool]:
    path = _task_path(settings, spec_id)
    result = _checked(settings.repo_root, ("git", "show", f"{base_ref}:{path}"), label="read canonical Task ledger")
    local_task_id = task_id.rsplit(":", 1)[-1]
    pattern = re.compile(rf"^\s*-\s*\[([ xX])\]\s+{re.escape(local_task_id)}\b", re.MULTILINE)
    matches = pattern.findall(result.stdout)
    if len(matches) != 1:
        raise PostPublicationError(
            f"Canonical Task {local_task_id} must appear exactly once in {path}; found {len(matches)}"
        )
    return path, matches[0].lower() == "x"


def _matching_lease(
    settings: GraphSettings,
    record: PublicationRecord,
    *,
    root_override: Path | None,
) -> ExecutionAllocation | None:
    root = execution_root(settings, root_override)
    registry = load_registry(root / "leases.json", expected_repository=settings.repository_id)
    lease = active_lease(registry, record.task_id)
    if lease is None:
        return None
    mismatches: list[str] = []
    if lease.repository != record.repository:
        mismatches.append("repository")
    if lease.spec_id != record.spec_id:
        mismatches.append("specId")
    if lease.branch != record.branch:
        mismatches.append("branch")
    if Path(lease.worktree_path).resolve() != Path(record.worktree_path).resolve():
        mismatches.append("worktreePath")
    if mismatches:
        raise PostPublicationError(
            f"Publication/active lease mismatch for {record.task_id}: {', '.join(mismatches)}"
        )
    return lease


def reconcile_post_publication(
    settings: GraphSettings,
    publication_id: str,
    *,
    root_override: Path | None = None,
) -> ReconciliationResult:
    record = load_publication_record(settings, publication_id, root_override=root_override)
    _assert_publication(record, settings)
    existing = load_receipt(settings, publication_id, root_override=root_override, required=False)

    pr = _inspect_pr(settings, record)
    pr_number = int(pr.get("number") or 0)
    merged_at = pr.get("mergedAt")
    merge_commit = pr.get("mergeCommit") or {}
    merge_sha = str(merge_commit.get("oid") or "") if isinstance(merge_commit, dict) else ""
    pr_merged = bool(merged_at and merge_sha and str(pr.get("state") or "").upper() == "MERGED")

    blockers: list[str] = []
    if not pr_merged:
        blockers.append("pull request is not merged")

    base_ref: str | None = None
    base_revision: str | None = None
    merge_reachable = False
    canonical_path: str | None = None
    canonical_completed = False
    if pr_merged:
        base_ref, base_revision = _refresh_base(settings, record.base_branch)
        merge_reachable = _merge_reachable(settings, merge_sha, base_ref)
        if not merge_reachable:
            blockers.append("merge commit is not reachable from refreshed base")
        else:
            canonical_path, canonical_completed = _canonical_task_completed(
                settings,
                base_ref=base_ref,
                spec_id=record.spec_id,
                task_id=record.task_id,
            )
            if not canonical_completed:
                blockers.append("canonical Task is not complete in merged base")

    lease = _matching_lease(settings, record, root_override=root_override)
    already_finalized = bool(existing and existing.status == "finalized" and existing.lease_released)
    lease_active = lease is not None
    if not lease_active and not already_finalized:
        blockers.append("matching active lease is missing")

    worktrees = list_worktrees(settings.repo_root)
    descriptor = find_worktree(worktrees, path=Path(record.worktree_path))
    worktree_registered = descriptor is not None
    worktree_dirty = is_worktree_dirty(Path(record.worktree_path)) if descriptor is not None else None

    return ReconciliationResult(
        repository=settings.repository_id,
        publication_id=record.publication_id,
        validation_id=record.validation_id,
        task_id=record.task_id,
        spec_id=record.spec_id,
        branch=record.branch,
        base_branch=record.base_branch,
        worktree_path=record.worktree_path,
        pr_url=record.pr_url or "",
        pr_number=pr_number,
        pr_merged=pr_merged,
        merge_commit_sha=merge_sha or None,
        base_revision=base_revision,
        merge_reachable=merge_reachable,
        canonical_task_path=canonical_path,
        canonical_task_completed=canonical_completed,
        lease_active=lease_active,
        worktree_registered=worktree_registered,
        worktree_dirty=worktree_dirty,
        already_finalized=already_finalized,
        finalizable=not blockers,
        blockers=tuple(blockers),
    )


def _receipt_from_result(result: ReconciliationResult) -> PostPublicationReceipt:
    if not result.finalizable:
        raise PostPublicationError("Cannot create finalization receipt from blocked reconciliation")
    if result.merge_commit_sha is None or result.base_revision is None or result.canonical_task_path is None:
        raise PostPublicationError("Reconciliation is missing required merge/canonical evidence")
    now = _utc_now()
    return PostPublicationReceipt(
        receipt_id=f"post-{result.publication_id}",
        repository=result.repository,
        publication_id=result.publication_id,
        validation_id=result.validation_id,
        task_id=result.task_id,
        spec_id=result.spec_id,
        branch=result.branch,
        base_branch=result.base_branch,
        worktree_path=result.worktree_path,
        pr_url=result.pr_url,
        pr_number=result.pr_number,
        merge_commit_sha=result.merge_commit_sha,
        base_revision=result.base_revision,
        canonical_task_path=result.canonical_task_path,
        canonical_task_completed=True,
        lease_released=False,
        worktree_removed=False,
        status="reconciled",
        created_at=now,
        updated_at=now,
    )


def finalize_post_publication(
    settings: GraphSettings,
    publication_id: str,
    *,
    release: bool,
    remove: bool = False,
    root_override: Path | None = None,
) -> PostPublicationReceipt:
    if remove and not release:
        raise PostPublicationError("--remove-worktree requires explicit --release-lease intent")
    if not release:
        raise PostPublicationError("Finalization requires explicit --release-lease intent")

    existing = load_receipt(settings, publication_id, root_override=root_override, required=False)
    if existing is not None and existing.status == "finalized" and existing.lease_released:
        if not remove or existing.worktree_removed:
            return existing

    result = reconcile_post_publication(settings, publication_id, root_override=root_override)
    if result.blockers and not result.already_finalized:
        raise PostPublicationError("Post-publication finalization blocked: " + "; ".join(result.blockers))

    receipt = existing or _receipt_from_result(result)
    now = _utc_now()

    if not receipt.lease_released:
        root = execution_root(settings, root_override)
        release_lease(root / "leases.json", repository=settings.repository_id, task_id=receipt.task_id)
        receipt = replace(receipt, lease_released=True, status="finalized", block_reason=None, updated_at=now, finished_at=now)
        save_receipt(settings, receipt, root_override=root_override)

    if remove and not receipt.worktree_removed:
        worktree_path = Path(receipt.worktree_path)
        descriptor = find_worktree(list_worktrees(settings.repo_root), path=worktree_path)
        if descriptor is None:
            if worktree_path.exists():
                blocked = replace(
                    receipt,
                    status="blocked",
                    block_reason="worktree path exists but is not registered with Git",
                    updated_at=_utc_now(),
                )
                save_receipt(settings, blocked, root_override=root_override)
                raise PostPublicationError(blocked.block_reason or "worktree cleanup blocked")
            receipt = replace(receipt, worktree_removed=True, status="finalized", block_reason=None, updated_at=_utc_now())
            save_receipt(settings, receipt, root_override=root_override)
            return receipt
        if is_worktree_dirty(worktree_path):
            blocked = replace(
                receipt,
                status="blocked",
                block_reason="worktree is dirty; V9 never force-removes dirty worktrees",
                updated_at=_utc_now(),
            )
            save_receipt(settings, blocked, root_override=root_override)
            raise PostPublicationError(blocked.block_reason or "worktree cleanup blocked")
        remove_worktree(settings.repo_root, worktree_path, force=False)
        receipt = replace(
            receipt,
            worktree_removed=True,
            status="finalized",
            block_reason=None,
            updated_at=_utc_now(),
            finished_at=receipt.finished_at or _utc_now(),
        )
        save_receipt(settings, receipt, root_override=root_override)

    if receipt.status != "finalized":
        receipt = replace(receipt, status="finalized", block_reason=None, updated_at=_utc_now(), finished_at=_utc_now())
        save_receipt(settings, receipt, root_override=root_override)
    return receipt
