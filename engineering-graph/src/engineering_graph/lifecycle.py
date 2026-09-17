from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable

from .config import GraphSettings, current_git_revision
from .execution import ExecutionAllocation
from .leases import active_lease, load_registry
from .post_publication import PostPublicationReceipt, load_receipt
from .publisher import PublicationRecord, list_publication_records
from .runner import AgentRun, latest_run, load_runner_registry, registry_path
from .supervisor import SupervisorJob, list_supervisor_jobs
from .validation import ValidationRecord, list_validation_records

ASSESSMENT_VERSION = "1"
PHASES = frozenset(
    {
        "unallocated",
        "allocated",
        "running",
        "executed",
        "validated",
        "published",
        "awaiting_human",
        "merged",
        "reconciled",
        "finalized",
        "blocked",
    }
)
NEXT_ACTIONS = frozenset(
    {
        "prepare_execution",
        "start_execution",
        "wait_for_execution",
        "repair_execution",
        "run_validation",
        "repair_validation",
        "run_publication",
        "resume_publication",
        "inspect_pr_state",
        "await_human_review",
        "await_human_gate",
        "remediate_human_gate",
        "reconcile_post_publication",
        "finalize_post_publication",
        "repair_cleanup",
        "repair_evidence",
        "none",
    }
)
HUMAN_GATE_STATUSES = frozenset({"PENDING", "PASSED", "FAILED", "WAIVED"})


class LifecycleError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LifecycleBlocker:
    code: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "detail": self.detail}


@dataclass(frozen=True, slots=True)
class HumanAsyncGate:
    gate_id: str
    subject: str
    trigger_evidence: str
    expected_observation: str
    approver: str
    status: str
    freshness_boundary: str
    next_action: str
    rationale: str | None = None
    required: bool = True

    def to_dict(self, *, head_sha: str) -> dict[str, Any]:
        return {
            "gateId": self.gate_id,
            "subject": self.subject,
            "triggerEvidence": self.trigger_evidence,
            "expectedObservation": self.expected_observation,
            "approver": self.approver,
            "status": self.status,
            "rationale": self.rationale,
            "freshnessBoundary": self.freshness_boundary,
            "fresh": self.is_fresh(head_sha),
            "nextAction": self.next_action,
            "required": self.required,
        }

    def is_fresh(self, head_sha: str) -> bool:
        return bool(head_sha and head_sha.lower() in self.freshness_boundary.lower())

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "HumanAsyncGate":
        gate = cls(
            gate_id=str(raw.get("gateId") or ""),
            subject=str(raw.get("subject") or ""),
            trigger_evidence=str(
                raw.get("triggerEvidence")
                or raw.get("trigger / evidence")
                or raw.get("trigger/evidence")
                or ""
            ),
            expected_observation=str(raw.get("expectedObservation") or ""),
            approver=str(raw.get("approver") or ""),
            status=str(raw.get("status") or "").upper(),
            rationale=(
                str(raw["rationale"]) if raw.get("rationale") is not None else None
            ),
            freshness_boundary=str(raw.get("freshnessBoundary") or ""),
            next_action=str(raw.get("nextAction") or ""),
            required=bool(raw.get("required", True)),
        )
        validate_human_gate(gate)
        return gate


def validate_human_gate(gate: HumanAsyncGate) -> None:
    required = {
        "gateId": gate.gate_id,
        "subject": gate.subject,
        "triggerEvidence": gate.trigger_evidence,
        "expectedObservation": gate.expected_observation,
        "approver": gate.approver,
        "freshnessBoundary": gate.freshness_boundary,
        "nextAction": gate.next_action,
    }
    missing = [name for name, value in required.items() if not value.strip()]
    if missing:
        raise LifecycleError(
            "Human Async Gate missing required fields: " + ", ".join(missing)
        )
    if gate.status not in HUMAN_GATE_STATUSES:
        raise LifecycleError(f"Unsupported Human Async Gate status: {gate.status}")
    if gate.status == "WAIVED" and not (gate.rationale or "").strip():
        raise LifecycleError("WAIVED Human Async Gate requires rationale")


@dataclass(frozen=True, slots=True)
class PrSnapshot:
    state: str
    url: str
    number: int | None
    base_branch: str
    head_branch: str
    merged: bool
    merge_commit_sha: str | None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "url": self.url,
            "number": self.number,
            "baseBranch": self.base_branch,
            "headBranch": self.head_branch,
            "merged": self.merged,
            "mergeCommitSha": self.merge_commit_sha,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class SupervisorSnapshot:
    job_id: str
    repository: str
    source_revision: str
    spec_id: str | None
    task_id: str
    status: str
    task_status: str
    run_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "jobId": self.job_id,
            "repository": self.repository,
            "sourceRevision": self.source_revision,
            "specId": self.spec_id,
            "taskId": self.task_id,
            "status": self.status,
            "taskStatus": self.task_status,
            "runIds": list(self.run_ids),
        }


@dataclass(frozen=True, slots=True)
class LifecycleEvidence:
    repository: str
    task_id: str
    spec_id: str
    head_sha: str
    base_branch: str
    allocation: ExecutionAllocation | None = None
    run: AgentRun | None = None
    supervisor: SupervisorSnapshot | None = None
    validation: ValidationRecord | None = None
    publication: PublicationRecord | None = None
    pr: PrSnapshot | None = None
    post_publication: PostPublicationReceipt | None = None
    human_gates: tuple[HumanAsyncGate, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical": {
                "repository": self.repository,
                "taskId": self.task_id,
                "specId": self.spec_id,
                "headSha": self.head_sha,
                "baseBranch": self.base_branch,
            },
            "derived": {
                "allocation": (
                    self.allocation.to_dict() if self.allocation is not None else None
                ),
                "run": self.run.to_dict() if self.run is not None else None,
                "supervisor": (
                    self.supervisor.to_dict() if self.supervisor is not None else None
                ),
                "validation": (
                    self.validation.to_dict() if self.validation is not None else None
                ),
                "publication": (
                    self.publication.to_dict() if self.publication is not None else None
                ),
                "pullRequest": self.pr.to_dict() if self.pr is not None else None,
                "postPublication": (
                    self.post_publication.to_dict()
                    if self.post_publication is not None
                    else None
                ),
            },
            "human": {
                "gates": [
                    gate.to_dict(head_sha=self.head_sha) for gate in self.human_gates
                ]
            },
        }


@dataclass(frozen=True, slots=True)
class LifecycleAssessment:
    repository: str
    task_id: str
    spec_id: str
    head_sha: str
    phase: str
    next_action: str
    blockers: tuple[LifecycleBlocker, ...]
    evidence: LifecycleEvidence
    assessment_version: str = ASSESSMENT_VERSION

    def to_dict(self) -> dict[str, Any]:
        continuation = build_continuation(self)
        return {
            "assessmentVersion": self.assessment_version,
            "repository": self.repository,
            "taskId": self.task_id,
            "specId": self.spec_id,
            "headSha": self.head_sha,
            "phase": self.phase,
            "nextAction": self.next_action,
            "blockers": [blocker.to_dict() for blocker in self.blockers],
            "evidence": self.evidence.to_dict(),
            "humanAsyncGates": [
                gate.to_dict(head_sha=self.head_sha)
                for gate in self.evidence.human_gates
            ],
            "continuation": continuation,
        }


def _validate_phase_action(phase: str, next_action: str) -> None:
    if phase not in PHASES:
        raise LifecycleError(f"Unsupported lifecycle phase: {phase}")
    if next_action not in NEXT_ACTIONS:
        raise LifecycleError(f"Unsupported lifecycle next action: {next_action}")


def _assessment(
    evidence: LifecycleEvidence,
    phase: str,
    next_action: str,
    blockers: Iterable[LifecycleBlocker] = (),
) -> LifecycleAssessment:
    _validate_phase_action(phase, next_action)
    return LifecycleAssessment(
        repository=evidence.repository,
        task_id=evidence.task_id,
        spec_id=evidence.spec_id,
        head_sha=evidence.head_sha,
        phase=phase,
        next_action=next_action,
        blockers=tuple(blockers),
        evidence=evidence,
    )


def _identity_conflicts(evidence: LifecycleEvidence) -> tuple[LifecycleBlocker, ...]:
    conflicts: list[str] = []

    def check(
        kind: str,
        repository: str | None,
        task_id: str | None,
        spec_id: str | None,
    ) -> None:
        if repository and repository != evidence.repository:
            conflicts.append(
                f"{kind}.repository={repository!r} expected={evidence.repository!r}"
            )
        if task_id and task_id != evidence.task_id:
            conflicts.append(
                f"{kind}.taskId={task_id!r} expected={evidence.task_id!r}"
            )
        if spec_id and spec_id != evidence.spec_id:
            conflicts.append(
                f"{kind}.specId={spec_id!r} expected={evidence.spec_id!r}"
            )

    if evidence.allocation is not None:
        check(
            "allocation",
            evidence.allocation.repository,
            evidence.allocation.task_id,
            evidence.allocation.spec_id,
        )
    if evidence.run is not None:
        check(
            "run",
            evidence.run.repository,
            evidence.run.task_id,
            evidence.run.spec_id,
        )
    if evidence.supervisor is not None:
        check(
            "supervisor",
            evidence.supervisor.repository,
            evidence.supervisor.task_id,
            evidence.supervisor.spec_id,
        )
    if evidence.validation is not None:
        check(
            "validation",
            evidence.validation.repository,
            evidence.validation.task_id,
            evidence.validation.spec_id,
        )
    if evidence.publication is not None:
        check(
            "publication",
            evidence.publication.repository,
            evidence.publication.task_id,
            evidence.publication.spec_id,
        )
    if evidence.post_publication is not None:
        check(
            "postPublication",
            evidence.post_publication.repository,
            evidence.post_publication.task_id,
            evidence.post_publication.spec_id,
        )

    branch_values: list[tuple[str, str]] = []
    worktree_values: list[tuple[str, str]] = []
    source_values: list[tuple[str, str]] = []

    def add_identity(
        kind: str,
        branch: str | None,
        worktree: str | None,
        source: str | None,
    ) -> None:
        if branch:
            branch_values.append((kind, branch))
        if worktree:
            worktree_values.append((kind, str(Path(worktree).resolve())))
        if source:
            source_values.append((kind, source))

    if evidence.allocation is not None:
        add_identity(
            "allocation",
            evidence.allocation.branch,
            evidence.allocation.worktree_path,
            evidence.allocation.source_revision,
        )
    if evidence.run is not None:
        add_identity(
            "run",
            evidence.run.branch,
            evidence.run.worktree_path,
            evidence.run.source_revision,
        )
    if evidence.validation is not None:
        add_identity(
            "validation",
            evidence.validation.branch,
            evidence.validation.worktree_path,
            evidence.validation.source_revision,
        )
    if evidence.publication is not None:
        add_identity(
            "publication",
            evidence.publication.branch,
            evidence.publication.worktree_path,
            evidence.publication.source_revision,
        )
    if evidence.post_publication is not None:
        add_identity(
            "postPublication",
            evidence.post_publication.branch,
            evidence.post_publication.worktree_path,
            None,
        )

    for label, values in (
        ("branch", branch_values),
        ("worktreePath", worktree_values),
        ("sourceRevision", source_values),
    ):
        distinct = {value for _, value in values}
        if len(distinct) > 1:
            rendered = ", ".join(f"{kind}={value!r}" for kind, value in values)
            conflicts.append(f"{label} conflict: {rendered}")

    if evidence.run is not None and evidence.validation is not None:
        if evidence.validation.run_id != evidence.run.run_id:
            conflicts.append(
                "validation.runId does not match latest runner runId: "
                f"{evidence.validation.run_id!r} != {evidence.run.run_id!r}"
            )
    if evidence.validation is not None and evidence.publication is not None:
        if evidence.publication.validation_id != evidence.validation.validation_id:
            conflicts.append(
                "publication.validationId does not match latest validationId: "
                f"{evidence.publication.validation_id!r} != "
                f"{evidence.validation.validation_id!r}"
            )
    if evidence.run is not None and evidence.publication is not None:
        if evidence.publication.run_id != evidence.run.run_id:
            conflicts.append(
                "publication.runId does not match latest runner runId: "
                f"{evidence.publication.run_id!r} != {evidence.run.run_id!r}"
            )
    if evidence.publication is not None and evidence.post_publication is not None:
        receipt = evidence.post_publication
        publication = evidence.publication
        if receipt.publication_id != publication.publication_id:
            conflicts.append(
                "postPublication.publicationId does not match publicationId"
            )
        if receipt.validation_id != publication.validation_id:
            conflicts.append(
                "postPublication.validationId does not match publication.validationId"
            )
        if receipt.base_branch != publication.base_branch:
            conflicts.append(
                "postPublication.baseBranch does not match publication.baseBranch"
            )
        if receipt.pr_url != (publication.pr_url or ""):
            conflicts.append("postPublication.prUrl does not match publication.prUrl")
    if evidence.publication is not None and evidence.pr is not None:
        publication = evidence.publication
        pr = evidence.pr
        if pr.url and publication.pr_url and pr.url != publication.pr_url:
            conflicts.append("pullRequest.url does not match publication.prUrl")
        if pr.base_branch and pr.base_branch != publication.base_branch:
            conflicts.append(
                "pullRequest.baseBranch does not match publication.baseBranch"
            )
        if pr.head_branch and pr.head_branch != publication.branch:
            conflicts.append(
                "pullRequest.headBranch does not match publication.branch"
            )

    return tuple(
        LifecycleBlocker("identity_conflict", detail) for detail in conflicts
    )


def _human_gate_blockers(
    evidence: LifecycleEvidence,
) -> tuple[tuple[LifecycleBlocker, ...], str | None]:
    blockers: list[LifecycleBlocker] = []
    action: str | None = None
    for gate in evidence.human_gates:
        if not gate.required:
            continue
        if gate.status == "FAILED":
            blockers.append(
                LifecycleBlocker(
                    "human_gate_failed",
                    f"{gate.gate_id} failed: {gate.subject}",
                )
            )
            action = "remediate_human_gate"
            continue
        fresh = gate.is_fresh(evidence.head_sha)
        if gate.status in {"PASSED", "WAIVED"} and not fresh:
            blockers.append(
                LifecycleBlocker(
                    "human_gate_stale",
                    f"{gate.gate_id} is stale for HEAD {evidence.head_sha}",
                )
            )
            if action != "remediate_human_gate":
                action = "await_human_gate"
            continue
        if gate.status == "PENDING":
            blockers.append(
                LifecycleBlocker(
                    "human_gate_pending",
                    f"{gate.gate_id} is pending: {gate.subject}",
                )
            )
            if action != "remediate_human_gate":
                action = "await_human_gate"
    return tuple(blockers), action


def assess_lifecycle(evidence: LifecycleEvidence) -> LifecycleAssessment:
    identity = _identity_conflicts(evidence)
    if identity:
        return _assessment(evidence, "blocked", "repair_evidence", identity)

    human_blockers, human_action = _human_gate_blockers(evidence)

    receipt = evidence.post_publication
    if receipt is not None:
        if receipt.status == "blocked":
            blocker = LifecycleBlocker(
                "post_publication_blocked",
                receipt.block_reason or "post-publication receipt is blocked",
            )
            return _assessment(
                evidence,
                "blocked",
                "repair_cleanup",
                (*human_blockers, blocker),
            )
        if human_action is not None:
            phase = (
                "blocked"
                if human_action == "remediate_human_gate"
                else "awaiting_human"
            )
            return _assessment(evidence, phase, human_action, human_blockers)
        if receipt.status == "finalized" and receipt.lease_released:
            return _assessment(evidence, "finalized", "none")
        if receipt.status == "reconciled":
            return _assessment(
                evidence, "reconciled", "finalize_post_publication"
            )

    publication = evidence.publication
    if publication is not None:
        if publication.status == "failed":
            blocker = LifecycleBlocker(
                "publication_failed",
                publication.error or "publication failed",
            )
            return _assessment(
                evidence,
                "blocked",
                "resume_publication",
                (blocker,),
            )
        if publication.status in {"started", "committed", "pushed"}:
            return _assessment(evidence, "published", "resume_publication")
        if publication.status == "pr_opened":
            if evidence.pr is None or evidence.pr.state == "unavailable":
                blocker = LifecycleBlocker(
                    "pr_state_unavailable",
                    (
                        evidence.pr.error
                        if evidence.pr is not None and evidence.pr.error
                        else "live PR state was not inspected"
                    ),
                )
                return _assessment(
                    evidence,
                    "published",
                    "inspect_pr_state",
                    (blocker,),
                )
            if human_action is not None:
                phase = (
                    "blocked"
                    if human_action == "remediate_human_gate"
                    else "awaiting_human"
                )
                return _assessment(evidence, phase, human_action, human_blockers)
            if evidence.pr.merged:
                return _assessment(
                    evidence, "merged", "reconcile_post_publication"
                )
            return _assessment(evidence, "awaiting_human", "await_human_review")

    validation = evidence.validation
    if validation is not None:
        if validation.status == "failed":
            blocker = LifecycleBlocker(
                "validation_failed",
                f"validation {validation.validation_id} failed",
            )
            return _assessment(
                evidence,
                "blocked",
                "repair_validation",
                (blocker,),
            )
        if validation.status == "passed" and validation.workspace_stable:
            return _assessment(evidence, "validated", "run_publication")

    run = evidence.run
    if run is not None:
        if run.status == "running":
            return _assessment(evidence, "running", "wait_for_execution")
        if run.status == "succeeded":
            return _assessment(evidence, "executed", "run_validation")
        if run.status in {"failed", "stopped", "orphaned"}:
            blocker = LifecycleBlocker(
                "runner_failed",
                f"runner {run.run_id} ended with status={run.status}",
            )
            return _assessment(
                evidence,
                "blocked",
                "repair_execution",
                (blocker,),
            )

    supervisor = evidence.supervisor
    if supervisor is not None and supervisor.task_status in {"exhausted", "stopped"}:
        blocker = LifecycleBlocker(
            "supervisor_exhausted",
            (
                f"supervisor {supervisor.job_id} task status="
                f"{supervisor.task_status}"
            ),
        )
        return _assessment(
            evidence,
            "blocked",
            "repair_execution",
            (blocker,),
        )

    if evidence.allocation is not None:
        return _assessment(evidence, "allocated", "start_execution")

    return _assessment(evidence, "unallocated", "prepare_execution")


def build_continuation(assessment: LifecycleAssessment) -> dict[str, Any]:
    evidence = assessment.evidence
    publication = evidence.publication
    branch = None
    if publication is not None:
        branch = publication.branch
    elif evidence.validation is not None:
        branch = evidence.validation.branch
    elif evidence.run is not None:
        branch = evidence.run.branch
    elif evidence.allocation is not None:
        branch = evidence.allocation.branch

    unresolved = [
        gate.to_dict(head_sha=evidence.head_sha)
        for gate in evidence.human_gates
        if gate.required
        and (
            gate.status in {"PENDING", "FAILED"}
            or (
                gate.status in {"PASSED", "WAIVED"}
                and not gate.is_fresh(evidence.head_sha)
            )
        )
    ]
    automated = {
        "allocation": (
            evidence.allocation.lease_status
            if evidence.allocation is not None
            else None
        ),
        "runner": evidence.run.status if evidence.run is not None else None,
        "supervisor": (
            evidence.supervisor.task_status
            if evidence.supervisor is not None
            else None
        ),
        "validation": (
            evidence.validation.status if evidence.validation is not None else None
        ),
        "publication": publication.status if publication is not None else None,
        "postPublication": (
            evidence.post_publication.status
            if evidence.post_publication is not None
            else None
        ),
    }
    return {
        "repository": evidence.repository,
        "baseBranch": evidence.base_branch,
        "branch": branch,
        "prUrl": publication.pr_url if publication is not None else None,
        "headSha": evidence.head_sha,
        "specId": evidence.spec_id,
        "taskId": evidence.task_id,
        "automatedState": automated,
        "unresolvedHumanAsyncGates": unresolved,
        "nextAction": assessment.next_action,
        "freshnessInstruction": (
            "Re-check repository HEAD, PR state and Human Async Gate evidence "
            "before acting; Git/current external state wins over this derived payload."
        ),
        "authorityBoundary": (
            "V10 is read-only projection; execute the next action only through "
            "its owning V3-V9 subsystem or human/external authority."
        ),
    }


def _load_human_gates(path: Path | None) -> tuple[HumanAsyncGate, ...]:
    if path is None:
        return ()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise LifecycleError(f"Human Async Gate file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise LifecycleError(
            f"Human Async Gate file is not valid JSON: {error}"
        ) from error
    if not isinstance(raw, list):
        raise LifecycleError("Human Async Gate file root must be a JSON array")
    gates = tuple(
        HumanAsyncGate.from_dict(item)
        for item in raw
        if isinstance(item, dict)
    )
    if len(gates) != len(raw):
        raise LifecycleError("Human Async Gate entries must be JSON objects")
    ids = [gate.gate_id for gate in gates]
    if len(ids) != len(set(ids)):
        raise LifecycleError("Human Async Gate file contains duplicate gateId values")
    return gates


def _supervisor_snapshot(
    jobs: Iterable[SupervisorJob], task_id: str
) -> SupervisorSnapshot | None:
    candidates: list[tuple[SupervisorJob, Any]] = []
    for job in jobs:
        for task in job.tasks:
            if task.task_id == task_id:
                candidates.append((job, task))
    if not candidates:
        return None
    job, task = sorted(
        candidates, key=lambda item: (item[0].created_at, item[0].job_id)
    )[-1]
    return SupervisorSnapshot(
        job_id=job.job_id,
        repository=job.repository,
        source_revision=job.source_revision,
        spec_id=job.spec_id,
        task_id=task.task_id,
        status=job.status,
        task_status=task.status,
        run_ids=task.run_ids,
    )


def _inspect_pr_read_only(
    settings: GraphSettings, publication: PublicationRecord
) -> PrSnapshot:
    if not publication.pr_url:
        return PrSnapshot(
            state="unavailable",
            url="",
            number=None,
            base_branch=publication.base_branch,
            head_branch=publication.branch,
            merged=False,
            merge_commit_sha=None,
            error="publication has no PR URL",
        )
    argv = [
        "gh",
        "pr",
        "view",
        publication.pr_url,
        "--json",
        "number,state,mergedAt,mergeCommit,url,baseRefName,headRefName",
    ]
    try:
        completed = subprocess.run(
            argv,
            cwd=settings.repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            shell=False,
            close_fds=True,
        )
    except OSError as error:
        return PrSnapshot(
            state="unavailable",
            url=publication.pr_url,
            number=None,
            base_branch=publication.base_branch,
            head_branch=publication.branch,
            merged=False,
            merge_commit_sha=None,
            error=f"PR inspection unavailable: {error}",
        )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "unknown error").strip()
        return PrSnapshot(
            state="unavailable",
            url=publication.pr_url,
            number=None,
            base_branch=publication.base_branch,
            head_branch=publication.branch,
            merged=False,
            merge_commit_sha=None,
            error=f"PR inspection failed: {detail[:1000]}",
        )
    try:
        raw = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return PrSnapshot(
            state="unavailable",
            url=publication.pr_url,
            number=None,
            base_branch=publication.base_branch,
            head_branch=publication.branch,
            merged=False,
            merge_commit_sha=None,
            error=f"PR inspection returned invalid JSON: {error}",
        )
    if not isinstance(raw, dict):
        return PrSnapshot(
            state="unavailable",
            url=publication.pr_url,
            number=None,
            base_branch=publication.base_branch,
            head_branch=publication.branch,
            merged=False,
            merge_commit_sha=None,
            error="PR inspection root must be a JSON object",
        )
    merge = raw.get("mergeCommit")
    merge_sha = str(merge.get("oid") or "") if isinstance(merge, dict) else ""
    state = str(raw.get("state") or "").upper()
    merged = bool(state == "MERGED" and raw.get("mergedAt") and merge_sha)
    return PrSnapshot(
        state=state or "UNKNOWN",
        url=str(raw.get("url") or publication.pr_url),
        number=int(raw["number"]) if raw.get("number") is not None else None,
        base_branch=str(raw.get("baseRefName") or publication.base_branch),
        head_branch=str(raw.get("headRefName") or publication.branch),
        merged=merged,
        merge_commit_sha=merge_sha or None,
    )


def collect_lifecycle_evidence(
    settings: GraphSettings,
    task_id: str,
    *,
    human_gates_path: Path | None = None,
    root_override: Path | None = None,
    inspect_pr: bool = True,
    base_branch: str = "master",
) -> LifecycleEvidence:
    if ":" not in task_id:
        raise LifecycleError(
            "Lifecycle task id must be canonical, for example SPEC-018-...:T001"
        )
    spec_id = task_id.rsplit(":", 1)[0]
    head_sha = current_git_revision(settings.repo_root) or ""
    if not head_sha:
        raise LifecycleError("Unable to resolve current repository HEAD")

    execution_root = (root_override or settings.tool_root / ".execution").resolve()
    lease_registry = load_registry(
        execution_root / "leases.json",
        expected_repository=settings.repository_id,
    )
    allocation = active_lease(lease_registry, task_id)

    runner_registry = load_runner_registry(
        registry_path(settings, root_override),
        expected_repository=settings.repository_id,
    )
    run = latest_run(runner_registry, task_id)

    supervisor = _supervisor_snapshot(
        list_supervisor_jobs(settings, root_override=root_override),
        task_id,
    )

    validations = list_validation_records(
        settings,
        task_id=task_id,
        root_override=root_override,
    )
    validation = validations[-1] if validations else None

    publications = list_publication_records(
        settings,
        task_id=task_id,
        root_override=root_override,
    )
    publication = publications[-1] if publications else None

    receipt = None
    pr = None
    effective_base = base_branch
    if publication is not None:
        effective_base = publication.base_branch
        receipt = load_receipt(
            settings,
            publication.publication_id,
            root_override=root_override,
            required=False,
        )
        if inspect_pr and publication.status == "pr_opened":
            pr = _inspect_pr_read_only(settings, publication)

    gates = _load_human_gates(human_gates_path)

    return LifecycleEvidence(
        repository=settings.repository_id,
        task_id=task_id,
        spec_id=spec_id,
        head_sha=head_sha,
        base_branch=effective_base,
        allocation=allocation,
        run=run,
        supervisor=supervisor,
        validation=validation,
        publication=publication,
        pr=pr,
        post_publication=receipt,
        human_gates=gates,
    )
