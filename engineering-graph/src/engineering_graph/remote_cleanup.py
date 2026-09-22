from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable

from .config import GraphSettings, normalize_repository_id
from .leases import LeaseRegistryError, load_registry
from .post_publication import PostPublicationReceipt, load_receipt as load_post_publication_receipt
from .publisher import PublicationRecord, load_publication_record
from .runner import execution_root
from .worktrees import GitWorktreeError, list_worktrees

ASSESSMENT_VERSION = "1"
RECEIPT_VERSION = "1"

REMOTE_STATES = frozenset({"present", "absent", "unavailable", "conflict"})
WORKTREE_STATES = frozenset({"none", "registered", "conflict", "unavailable"})
NEXT_ACTIONS = frozenset(
    {
        "delete_remote_branch",
        "finish_local_cleanup",
        "repair_evidence",
        "inspect_remote_policy",
        "retry_remote_inspection",
        "none",
    }
)
RECEIPT_OUTCOMES = frozenset({"deleted", "already_absent", "blocked", "failed"})
BLOCKERS = frozenset(
    {
        "publication_not_terminal",
        "publication_missing_commit_sha",
        "v9_not_finalized",
        "evidence_repository_mismatch",
        "evidence_publication_mismatch",
        "evidence_validation_mismatch",
        "evidence_task_mismatch",
        "evidence_spec_mismatch",
        "evidence_branch_mismatch",
        "evidence_base_branch_mismatch",
        "evidence_worktree_mismatch",
        "evidence_pr_mismatch",
        "invalid_target_ref",
        "target_is_base_branch",
        "target_is_default_branch",
        "default_branch_unresolved",
        "remote_repository_mismatch",
        "active_matching_lease",
        "active_local_identity_conflict",
        "matching_worktree_registered",
        "local_state_unavailable",
        "remote_unavailable",
        "remote_ref_malformed",
        "remote_sha_mismatch",
    }
)

_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_PR_NUMBER_RE = re.compile(r"/pull/([1-9][0-9]*)(?:[/?#]|$)")


class RemoteCleanupError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RemoteBranchIdentity:
    repository: str
    remote: str
    branch: str
    full_ref: str
    expected_sha: str
    base_branch: str
    default_branch: str | None
    publication_id: str
    spec_id: str
    task_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "remote": self.remote,
            "branch": self.branch,
            "fullRef": self.full_ref,
            "expectedSha": self.expected_sha,
            "baseBranch": self.base_branch,
            "defaultBranch": self.default_branch,
            "publicationId": self.publication_id,
            "specId": self.spec_id,
            "taskId": self.task_id,
        }


@dataclass(frozen=True, slots=True)
class RemoteCleanupAssessment:
    identity: RemoteBranchIdentity
    v9_finalized: bool
    active_lease: bool
    matching_worktree_state: str
    remote_state: str
    observed_sha: str | None
    ready: bool
    terminal_without_mutation: bool
    blockers: tuple[str, ...]
    next_action: str
    observed_at: str
    assessment_version: str = ASSESSMENT_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "assessmentVersion": self.assessment_version,
            **self.identity.to_dict(),
            "v9Finalized": self.v9_finalized,
            "activeLease": self.active_lease,
            "matchingWorktreeState": self.matching_worktree_state,
            "remoteState": self.remote_state,
            "observedSha": self.observed_sha,
            "ready": self.ready,
            "terminalWithoutMutation": self.terminal_without_mutation,
            "blockers": list(self.blockers),
            "nextAction": self.next_action,
            "observedAt": self.observed_at,
        }
        return payload


@dataclass(frozen=True, slots=True)
class RemoteCleanupReceipt:
    receipt_id: str
    repository: str
    publication_id: str
    spec_id: str
    task_id: str
    remote: str
    branch: str
    expected_sha: str
    observed_sha_before: str | None
    outcome: str
    created_at: str
    updated_at: str
    block_reason: str | None = None
    error: str | None = None
    finished_at: str | None = None
    receipt_version: str = RECEIPT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "receiptVersion": self.receipt_version,
            "receiptId": self.receipt_id,
            "repository": self.repository,
            "publicationId": self.publication_id,
            "specId": self.spec_id,
            "taskId": self.task_id,
            "remote": self.remote,
            "branch": self.branch,
            "expectedSha": self.expected_sha,
            "observedShaBefore": self.observed_sha_before,
            "outcome": self.outcome,
            "blockReason": self.block_reason,
            "error": self.error,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "finishedAt": self.finished_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RemoteCleanupReceipt":
        return cls(
            receipt_id=str(raw.get("receiptId") or ""),
            repository=str(raw.get("repository") or ""),
            publication_id=str(raw.get("publicationId") or ""),
            spec_id=str(raw.get("specId") or ""),
            task_id=str(raw.get("taskId") or ""),
            remote=str(raw.get("remote") or ""),
            branch=str(raw.get("branch") or ""),
            expected_sha=str(raw.get("expectedSha") or ""),
            observed_sha_before=(
                str(raw["observedShaBefore"]) if raw.get("observedShaBefore") is not None else None
            ),
            outcome=str(raw.get("outcome") or ""),
            block_reason=str(raw["blockReason"]) if raw.get("blockReason") is not None else None,
            error=str(raw["error"]) if raw.get("error") is not None else None,
            created_at=str(raw.get("createdAt") or ""),
            updated_at=str(raw.get("updatedAt") or ""),
            finished_at=str(raw["finishedAt"]) if raw.get("finishedAt") is not None else None,
            receipt_version=str(raw.get("receiptVersion") or ""),
        )


@dataclass(frozen=True, slots=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_command(cwd: Path, argv: Iterable[str]) -> CommandResult:
    values = tuple(str(value) for value in argv)
    if not values:
        raise RemoteCleanupError("Remote-cleanup command argv cannot be empty")
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


def _add_blocker(blockers: list[str], blocker: str) -> None:
    if blocker not in BLOCKERS:
        raise RemoteCleanupError(f"Unsupported remote-cleanup blocker: {blocker}")
    if blocker not in blockers:
        blockers.append(blocker)


def validate_remote_cleanup_receipt(receipt: RemoteCleanupReceipt) -> None:
    if receipt.receipt_version != RECEIPT_VERSION:
        raise RemoteCleanupError(f"Unsupported remote-cleanup receipt version: {receipt.receipt_version}")
    required = {
        "receiptId": receipt.receipt_id,
        "repository": receipt.repository,
        "publicationId": receipt.publication_id,
        "specId": receipt.spec_id,
        "taskId": receipt.task_id,
        "remote": receipt.remote,
        "branch": receipt.branch,
        "expectedSha": receipt.expected_sha,
        "createdAt": receipt.created_at,
        "updatedAt": receipt.updated_at,
    }
    missing = [name for name, value in required.items() if not str(value).strip()]
    if missing:
        raise RemoteCleanupError(
            f"Remote-cleanup receipt missing required fields: {', '.join(missing)}"
        )
    if not _SHA_RE.fullmatch(receipt.expected_sha):
        raise RemoteCleanupError("Remote-cleanup receipt requires a 40-hex expectedSha")
    if receipt.observed_sha_before is not None and not _SHA_RE.fullmatch(receipt.observed_sha_before):
        raise RemoteCleanupError("Remote-cleanup receipt observedShaBefore must be 40-hex when present")
    if receipt.outcome not in RECEIPT_OUTCOMES:
        raise RemoteCleanupError(f"Unsupported remote-cleanup receipt outcome: {receipt.outcome}")
    if receipt.outcome == "deleted" and receipt.observed_sha_before != receipt.expected_sha:
        raise RemoteCleanupError("Deleted receipt requires observedShaBefore == expectedSha")
    if receipt.outcome == "already_absent" and receipt.observed_sha_before is not None:
        raise RemoteCleanupError("already_absent receipt cannot record observedShaBefore")
    if receipt.outcome == "blocked" and not (receipt.block_reason or "").strip():
        raise RemoteCleanupError("Blocked remote-cleanup receipt requires blockReason")
    if receipt.outcome == "failed" and not (receipt.error or "").strip():
        raise RemoteCleanupError("Failed remote-cleanup receipt requires error")


def validate_remote_cleanup_assessment(assessment: RemoteCleanupAssessment) -> None:
    if assessment.assessment_version != ASSESSMENT_VERSION:
        raise RemoteCleanupError(
            f"Unsupported remote-cleanup assessment version: {assessment.assessment_version}"
        )
    identity = assessment.identity
    required = {
        "repository": identity.repository,
        "remote": identity.remote,
        "branch": identity.branch,
        "fullRef": identity.full_ref,
        "baseBranch": identity.base_branch,
        "publicationId": identity.publication_id,
        "specId": identity.spec_id,
        "taskId": identity.task_id,
        "observedAt": assessment.observed_at,
    }
    missing = [name for name, value in required.items() if not str(value).strip()]
    if missing:
        raise RemoteCleanupError(
            f"Remote-cleanup assessment missing required fields: {', '.join(missing)}"
        )
    if identity.full_ref != f"refs/heads/{identity.branch}":
        raise RemoteCleanupError("Remote-cleanup fullRef must be derived from branch")
    if identity.expected_sha and not _SHA_RE.fullmatch(identity.expected_sha):
        raise RemoteCleanupError("Remote-cleanup expectedSha must be 40-hex when present")
    if assessment.observed_sha is not None and not _SHA_RE.fullmatch(assessment.observed_sha):
        raise RemoteCleanupError("Remote-cleanup observedSha must be 40-hex when present")
    if assessment.remote_state not in REMOTE_STATES:
        raise RemoteCleanupError(f"Unsupported remoteState: {assessment.remote_state}")
    if assessment.matching_worktree_state not in WORKTREE_STATES:
        raise RemoteCleanupError(
            f"Unsupported matchingWorktreeState: {assessment.matching_worktree_state}"
        )
    if assessment.next_action not in NEXT_ACTIONS:
        raise RemoteCleanupError(f"Unsupported nextAction: {assessment.next_action}")
    invalid_blockers = [value for value in assessment.blockers if value not in BLOCKERS]
    if invalid_blockers:
        raise RemoteCleanupError(
            f"Unsupported remote-cleanup blockers: {', '.join(invalid_blockers)}"
        )
    if len(set(assessment.blockers)) != len(assessment.blockers):
        raise RemoteCleanupError("Remote-cleanup blockers must be unique")
    if assessment.ready:
        if assessment.blockers:
            raise RemoteCleanupError("ready assessment cannot contain blockers")
        if assessment.remote_state != "present":
            raise RemoteCleanupError("ready assessment requires remoteState=present")
        if assessment.observed_sha != identity.expected_sha:
            raise RemoteCleanupError("ready assessment requires observedSha == expectedSha")
        if assessment.next_action != "delete_remote_branch":
            raise RemoteCleanupError("ready assessment requires delete_remote_branch nextAction")
    if assessment.terminal_without_mutation:
        if assessment.blockers:
            raise RemoteCleanupError("terminalWithoutMutation assessment cannot contain blockers")
        if assessment.remote_state != "absent":
            raise RemoteCleanupError("terminalWithoutMutation requires remoteState=absent")
        if assessment.next_action != "none":
            raise RemoteCleanupError("terminalWithoutMutation requires nextAction=none")
    if assessment.ready and assessment.terminal_without_mutation:
        raise RemoteCleanupError("Assessment cannot be both ready and terminalWithoutMutation")


def _pr_number(url: str | None) -> int | None:
    if not url:
        return None
    match = _PR_NUMBER_RE.search(url)
    return int(match.group(1)) if match else None


def _evidence_blockers(
    settings: GraphSettings,
    publication: PublicationRecord,
    receipt: PostPublicationReceipt,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if publication.status != "pr_opened" or not publication.pr_url:
        _add_blocker(blockers, "publication_not_terminal")
    if not publication.commit_sha or not _SHA_RE.fullmatch(publication.commit_sha):
        _add_blocker(blockers, "publication_missing_commit_sha")
    if receipt.status != "finalized" or not receipt.lease_released or not receipt.canonical_task_completed:
        _add_blocker(blockers, "v9_not_finalized")

    if (
        publication.repository.lower() != settings.repository_id.lower()
        or receipt.repository.lower() != publication.repository.lower()
    ):
        _add_blocker(blockers, "evidence_repository_mismatch")
    if receipt.publication_id != publication.publication_id:
        _add_blocker(blockers, "evidence_publication_mismatch")
    if receipt.validation_id != publication.validation_id:
        _add_blocker(blockers, "evidence_validation_mismatch")
    if receipt.task_id != publication.task_id:
        _add_blocker(blockers, "evidence_task_mismatch")
    if receipt.spec_id != publication.spec_id:
        _add_blocker(blockers, "evidence_spec_mismatch")
    if receipt.branch != publication.branch:
        _add_blocker(blockers, "evidence_branch_mismatch")
    if receipt.base_branch != publication.base_branch:
        _add_blocker(blockers, "evidence_base_branch_mismatch")
    if Path(receipt.worktree_path).resolve() != Path(publication.worktree_path).resolve():
        _add_blocker(blockers, "evidence_worktree_mismatch")
    if receipt.pr_url != (publication.pr_url or ""):
        _add_blocker(blockers, "evidence_pr_mismatch")
    publication_pr_number = _pr_number(publication.pr_url)
    if publication_pr_number is None or publication_pr_number != receipt.pr_number:
        _add_blocker(blockers, "evidence_pr_mismatch")
    return tuple(blockers)


def _target_ref_valid(settings: GraphSettings, full_ref: str) -> bool:
    result = _run_command(settings.repo_root, ("git", "check-ref-format", full_ref))
    return result.returncode == 0


def _remote_repository_matches(settings: GraphSettings, remote: str) -> tuple[bool, bool]:
    result = _run_command(settings.repo_root, ("git", "remote", "get-url", remote))
    if result.returncode != 0 or not result.stdout.strip():
        return False, False
    actual = normalize_repository_id(result.stdout.strip())
    return True, actual.lower() == settings.repository_id.lower()


def _resolve_default_branch(
    settings: GraphSettings,
    remote: str,
) -> tuple[str | None, str | None]:
    local = _run_command(
        settings.repo_root,
        ("git", "symbolic-ref", "--quiet", f"refs/remotes/{remote}/HEAD"),
    )
    if local.returncode == 0:
        value = local.stdout.strip()
        prefix = f"refs/remotes/{remote}/"
        if value.startswith(prefix) and len(value) > len(prefix):
            return value[len(prefix) :], None

    remote_head = _run_command(
        settings.repo_root,
        ("git", "ls-remote", "--symref", remote, "HEAD"),
    )
    if remote_head.returncode != 0:
        return None, "remote_unavailable"
    for raw_line in remote_head.stdout.splitlines():
        left, separator, right = raw_line.partition("\t")
        if separator and right == "HEAD" and left.startswith("ref: refs/heads/"):
            branch = left.removeprefix("ref: refs/heads/").strip()
            if branch:
                return branch, None
    return None, "default_branch_unresolved"


def _local_ownership(
    settings: GraphSettings,
    publication: PublicationRecord,
    *,
    root_override: Path | None,
) -> tuple[bool, str, tuple[str, ...]]:
    blockers: list[str] = []
    active_matching_lease = False
    worktree_state = "none"

    try:
        registry = load_registry(
            execution_root(settings, root_override) / "leases.json",
            expected_repository=settings.repository_id,
        )
        publication_path = Path(publication.worktree_path).resolve()
        for lease in registry.active:
            lease_path = Path(lease.worktree_path).resolve()
            overlaps = (
                lease.task_id == publication.task_id
                or lease.branch == publication.branch
                or lease_path == publication_path
            )
            if not overlaps:
                continue
            exact = (
                lease.repository.lower() == publication.repository.lower()
                and lease.task_id == publication.task_id
                and lease.spec_id == publication.spec_id
                and lease.branch == publication.branch
                and lease_path == publication_path
            )
            if exact:
                active_matching_lease = True
                _add_blocker(blockers, "active_matching_lease")
            else:
                _add_blocker(blockers, "active_local_identity_conflict")
    except LeaseRegistryError:
        _add_blocker(blockers, "local_state_unavailable")

    try:
        publication_path = Path(publication.worktree_path).resolve()
        for descriptor in list_worktrees(settings.repo_root):
            path_matches = descriptor.path == publication_path
            branch_matches = descriptor.branch == publication.branch
            if not (path_matches or branch_matches):
                continue
            if path_matches and branch_matches:
                worktree_state = "registered"
                _add_blocker(blockers, "matching_worktree_registered")
            else:
                worktree_state = "conflict"
                _add_blocker(blockers, "active_local_identity_conflict")
    except GitWorktreeError:
        worktree_state = "unavailable"
        _add_blocker(blockers, "local_state_unavailable")

    return active_matching_lease, worktree_state, tuple(blockers)


def inspect_remote_branch(
    settings: GraphSettings,
    *,
    remote: str,
    full_ref: str,
    expected_sha: str,
) -> tuple[str, str | None, str | None]:
    result = _run_command(
        settings.repo_root,
        ("git", "ls-remote", "--refs", remote, full_ref),
    )
    if result.returncode != 0:
        return "unavailable", None, "remote_unavailable"

    rows = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not rows:
        return "absent", None, None
    if len(rows) != 1:
        return "conflict", None, "remote_ref_malformed"

    sha, separator, observed_ref = rows[0].partition("\t")
    sha = sha.strip().lower()
    observed_ref = observed_ref.strip()
    if not separator or observed_ref != full_ref or not _SHA_RE.fullmatch(sha):
        return "conflict", sha if _SHA_RE.fullmatch(sha) else None, "remote_ref_malformed"
    if sha != expected_sha.lower():
        return "conflict", sha, "remote_sha_mismatch"
    return "present", sha, None


def _next_action(blockers: tuple[str, ...], remote_state: str) -> str:
    if not blockers:
        if remote_state == "present":
            return "delete_remote_branch"
        if remote_state == "absent":
            return "none"
        if remote_state == "unavailable":
            return "retry_remote_inspection"
        return "repair_evidence"

    local_blockers = {
        "active_matching_lease",
        "active_local_identity_conflict",
        "matching_worktree_registered",
        "local_state_unavailable",
    }
    if any(blocker in local_blockers for blocker in blockers):
        return "finish_local_cleanup"
    if "remote_unavailable" in blockers or "default_branch_unresolved" in blockers:
        return "retry_remote_inspection"
    return "repair_evidence"


def assess_remote_cleanup(
    settings: GraphSettings,
    publication_id: str,
    *,
    remote: str = "origin",
    root_override: Path | None = None,
) -> RemoteCleanupAssessment:
    if not publication_id.strip() or "/" in publication_id or "\\" in publication_id:
        raise RemoteCleanupError("Invalid publication id")
    if not remote.strip() or remote.startswith("-"):
        raise RemoteCleanupError("Invalid remote name")

    publication = load_publication_record(
        settings,
        publication_id,
        root_override=root_override,
    )
    receipt = load_post_publication_receipt(
        settings,
        publication_id,
        root_override=root_override,
        required=True,
    )
    if receipt is None:
        raise RemoteCleanupError(f"Finalized V9 receipt not found: {publication_id}")

    blockers = list(_evidence_blockers(settings, publication, receipt))
    expected_sha = (publication.commit_sha or "").lower()
    full_ref = f"refs/heads/{publication.branch}"
    default_branch: str | None = None
    active_lease = False
    matching_worktree_state = "none"
    remote_state = "conflict"
    observed_sha: str | None = None

    if not _target_ref_valid(settings, full_ref):
        _add_blocker(blockers, "invalid_target_ref")
    if publication.branch == publication.base_branch:
        _add_blocker(blockers, "target_is_base_branch")

    remote_exists, remote_matches = _remote_repository_matches(settings, remote)
    if not remote_exists:
        _add_blocker(blockers, "remote_unavailable")
    elif not remote_matches:
        _add_blocker(blockers, "remote_repository_mismatch")

    if not blockers or set(blockers).issubset(
        {
            "remote_unavailable",
            "remote_repository_mismatch",
            "target_is_base_branch",
            "invalid_target_ref",
        }
    ):
        default_branch, default_blocker = _resolve_default_branch(settings, remote)
        if default_blocker is not None:
            _add_blocker(blockers, default_blocker)
        if default_branch is not None and publication.branch == default_branch:
            _add_blocker(blockers, "target_is_default_branch")

    evidence_hard_blockers = {
        "publication_not_terminal",
        "publication_missing_commit_sha",
        "v9_not_finalized",
        "evidence_repository_mismatch",
        "evidence_publication_mismatch",
        "evidence_validation_mismatch",
        "evidence_task_mismatch",
        "evidence_spec_mismatch",
        "evidence_branch_mismatch",
        "evidence_base_branch_mismatch",
        "evidence_worktree_mismatch",
        "evidence_pr_mismatch",
        "invalid_target_ref",
        "target_is_base_branch",
        "target_is_default_branch",
        "remote_repository_mismatch",
    }

    if not any(blocker in evidence_hard_blockers for blocker in blockers):
        active_lease, matching_worktree_state, local_blockers = _local_ownership(
            settings,
            publication,
            root_override=root_override,
        )
        for blocker in local_blockers:
            _add_blocker(blockers, blocker)

    if not any(blocker in evidence_hard_blockers for blocker in blockers):
        remote_state, observed_sha, remote_blocker = inspect_remote_branch(
            settings,
            remote=remote,
            full_ref=full_ref,
            expected_sha=expected_sha,
        )
        if remote_blocker is not None:
            _add_blocker(blockers, remote_blocker)
    elif "remote_unavailable" in blockers:
        remote_state = "unavailable"

    ordered_blockers = tuple(blockers)
    ready = remote_state == "present" and not ordered_blockers
    terminal_without_mutation = remote_state == "absent" and not ordered_blockers
    assessment = RemoteCleanupAssessment(
        identity=RemoteBranchIdentity(
            repository=publication.repository,
            remote=remote,
            branch=publication.branch,
            full_ref=full_ref,
            expected_sha=expected_sha,
            base_branch=publication.base_branch,
            default_branch=default_branch,
            publication_id=publication.publication_id,
            spec_id=publication.spec_id,
            task_id=publication.task_id,
        ),
        v9_finalized=receipt.status == "finalized",
        active_lease=active_lease,
        matching_worktree_state=matching_worktree_state,
        remote_state=remote_state,
        observed_sha=observed_sha,
        ready=ready,
        terminal_without_mutation=terminal_without_mutation,
        blockers=ordered_blockers,
        next_action=_next_action(ordered_blockers, remote_state),
        observed_at=_utc_now(),
    )
    validate_remote_cleanup_assessment(assessment)
    return assessment
