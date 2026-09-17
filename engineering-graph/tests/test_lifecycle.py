from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from engineering_graph.execution import ExecutionAllocation
from engineering_graph.lifecycle import (
    HUMAN_GATE_STATUSES,
    NEXT_ACTIONS,
    PHASES,
    HumanAsyncGate,
    LifecycleError,
    LifecycleEvidence,
    PrSnapshot,
    _inspect_pr_read_only,
    _load_human_gates,
    assess_lifecycle,
    collect_lifecycle_evidence,
)
from engineering_graph.post_publication import PostPublicationReceipt
from engineering_graph.publisher import PublicationRecord
from engineering_graph.runner import AgentRun
from engineering_graph.validation import ValidationCommandResult, ValidationRecord

NOW = "2026-09-17T12:00:00+00:00"
HEAD = "a" * 40
REPO = "example/repo"
SPEC = "SPEC-018-LIFECYCLE-COORDINATOR"
TASK = f"{SPEC}:T008"
BRANCH = "exec/spec-018-t008"
WORKTREE = "/tmp/spec-018-t008"


def allocation(**changes) -> ExecutionAllocation:
    values = dict(
        repository=REPO,
        task_id=TASK,
        spec_id=SPEC,
        source_revision="source-sha",
        agent="codex",
        branch=BRANCH,
        worktree_path=WORKTREE,
        context_path="/tmp/context.json",
        handoff_path="/tmp/codex.md",
        lease_status="active",
        validation_commands=("python -m unittest",),
        created_at=NOW,
        updated_at=NOW,
    )
    values.update(changes)
    return ExecutionAllocation(**values)


def run(**changes) -> AgentRun:
    values = dict(
        run_id="run-1",
        repository=REPO,
        task_id=TASK,
        spec_id=SPEC,
        source_revision="source-sha",
        agent="codex",
        branch=BRANCH,
        worktree_path=WORKTREE,
        handoff_path="/tmp/codex.md",
        context_path="/tmp/context.json",
        argv=("codex",),
        stdin_handoff=False,
        pid=123,
        process_fingerprint=None,
        process_group_id=123,
        status="succeeded",
        exit_code=0,
        stop_requested=False,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        result_path="/tmp/result.json",
        created_at=NOW,
        started_at=NOW,
        finished_at=NOW,
        updated_at=NOW,
    )
    values.update(changes)
    return AgentRun(**values)


def validation(**changes) -> ValidationRecord:
    command = ValidationCommandResult(
        index=1,
        command="python -m unittest",
        argv=("python", "-m", "unittest"),
        status="passed",
        exit_code=0,
        stdout_path="/tmp/validation.out",
        stderr_path="/tmp/validation.err",
        started_at=NOW,
        finished_at=NOW,
    )
    values = dict(
        validation_id="val-1",
        repository=REPO,
        task_id=TASK,
        spec_id=SPEC,
        source_revision="source-sha",
        run_id="run-1",
        branch=BRANCH,
        worktree_path=WORKTREE,
        workspace_revision="workspace-sha",
        workspace_fingerprint_before="fingerprint",
        workspace_fingerprint_after="fingerprint",
        workspace_stable=True,
        status="passed",
        commands=(command,),
        created_at=NOW,
        finished_at=NOW,
    )
    values.update(changes)
    return ValidationRecord(**values)


def publication(**changes) -> PublicationRecord:
    values = dict(
        publication_id="pub-1",
        repository=REPO,
        task_id=TASK,
        spec_id=SPEC,
        validation_id="val-1",
        run_id="run-1",
        source_revision="source-sha",
        workspace_revision="workspace-sha",
        workspace_fingerprint="fingerprint",
        branch=BRANCH,
        base_branch="master",
        worktree_path=WORKTREE,
        commit_message="feat: lifecycle",
        pr_title="feat: lifecycle",
        pr_body="body",
        status="pr_opened",
        created_at=NOW,
        updated_at=NOW,
        last_successful_phase="pr",
        commit_sha="commit-sha",
        pr_url="https://github.com/example/repo/pull/1",
        finished_at=NOW,
    )
    values.update(changes)
    return PublicationRecord(**values)


def receipt(**changes) -> PostPublicationReceipt:
    values = dict(
        receipt_id="post-pub-1",
        repository=REPO,
        publication_id="pub-1",
        validation_id="val-1",
        task_id=TASK,
        spec_id=SPEC,
        branch=BRANCH,
        base_branch="master",
        worktree_path=WORKTREE,
        pr_url="https://github.com/example/repo/pull/1",
        pr_number=1,
        merge_commit_sha="merge-sha",
        base_revision="base-sha",
        canonical_task_path="specs/018-lifecycle-coordinator/tasks.md",
        canonical_task_completed=True,
        lease_released=False,
        worktree_removed=False,
        status="reconciled",
        created_at=NOW,
        updated_at=NOW,
    )
    values.update(changes)
    return PostPublicationReceipt(**values)


def pr(*, merged: bool = False) -> PrSnapshot:
    return PrSnapshot(
        state="MERGED" if merged else "OPEN",
        url="https://github.com/example/repo/pull/1",
        number=1,
        base_branch="master",
        head_branch=BRANCH,
        merged=merged,
        merge_commit_sha="merge-sha" if merged else None,
    )


def gate(status: str, **changes) -> HumanAsyncGate:
    values = dict(
        gate_id="HAG-001",
        subject="manual preview smoke",
        trigger_evidence="preview-1",
        expected_observation="critical journey succeeds",
        approver="repository owner",
        status=status,
        freshness_boundary=f"HEAD {HEAD}",
        next_action="record result",
        rationale="owner waived" if status == "WAIVED" else None,
        required=True,
    )
    values.update(changes)
    return HumanAsyncGate(**values)


def evidence(**changes) -> LifecycleEvidence:
    values = dict(
        repository=REPO,
        task_id=TASK,
        spec_id=SPEC,
        head_sha=HEAD,
        base_branch="master",
    )
    values.update(changes)
    return LifecycleEvidence(**values)


class LifecycleReducerTests(unittest.TestCase):
    def test_vocabularies_are_closed_and_versioned_by_contract(self) -> None:
        self.assertIn("blocked", PHASES)
        self.assertIn("finalized", PHASES)
        self.assertIn("start_execution", NEXT_ACTIONS)
        self.assertEqual(
            HUMAN_GATE_STATUSES,
            frozenset({"PENDING", "PASSED", "FAILED", "WAIVED"}),
        )

    def test_pipeline_phases_do_not_skip_authority_tiers(self) -> None:
        cases = (
            (evidence(), ("unallocated", "prepare_execution")),
            (
                evidence(allocation=allocation()),
                ("allocated", "start_execution"),
            ),
            (
                evidence(
                    allocation=allocation(),
                    run=run(status="running", exit_code=None, finished_at=None),
                ),
                ("running", "wait_for_execution"),
            ),
            (
                evidence(allocation=allocation(), run=run()),
                ("executed", "run_validation"),
            ),
            (
                evidence(
                    allocation=allocation(),
                    run=run(),
                    validation=validation(),
                ),
                ("validated", "run_publication"),
            ),
            (
                evidence(
                    allocation=allocation(),
                    run=run(),
                    validation=validation(),
                    publication=publication(),
                ),
                ("published", "inspect_pr_state"),
            ),
            (
                evidence(
                    allocation=allocation(),
                    run=run(),
                    validation=validation(),
                    publication=publication(),
                    pr=pr(),
                ),
                ("awaiting_human", "await_human_review"),
            ),
            (
                evidence(
                    allocation=allocation(),
                    run=run(),
                    validation=validation(),
                    publication=publication(),
                    pr=pr(merged=True),
                ),
                ("merged", "reconcile_post_publication"),
            ),
            (
                evidence(
                    run=run(),
                    validation=validation(),
                    publication=publication(),
                    pr=pr(merged=True),
                    post_publication=receipt(),
                ),
                ("reconciled", "finalize_post_publication"),
            ),
            (
                evidence(
                    run=run(),
                    validation=validation(),
                    publication=publication(),
                    pr=pr(merged=True),
                    post_publication=receipt(
                        status="finalized",
                        lease_released=True,
                        finished_at=NOW,
                    ),
                ),
                ("finalized", "none"),
            ),
        )
        for item, expected in cases:
            with self.subTest(expected=expected):
                assessment = assess_lifecycle(item)
                self.assertEqual(
                    (assessment.phase, assessment.next_action),
                    expected,
                )

    def test_identity_conflict_fails_closed(self) -> None:
        assessment = assess_lifecycle(
            evidence(
                allocation=allocation(),
                run=run(branch="exec/other"),
            )
        )
        self.assertEqual(assessment.phase, "blocked")
        self.assertEqual(assessment.next_action, "repair_evidence")
        self.assertTrue(
            any(item.code == "identity_conflict" for item in assessment.blockers)
        )

    def test_failed_lower_tiers_do_not_look_successful(self) -> None:
        runner_failed = assess_lifecycle(
            evidence(allocation=allocation(), run=run(status="failed", exit_code=1))
        )
        self.assertEqual(
            (runner_failed.phase, runner_failed.next_action),
            ("blocked", "repair_execution"),
        )

        failed_command = replace(
            validation().commands[0],
            status="failed",
            exit_code=1,
        )
        validation_failed = assess_lifecycle(
            evidence(
                allocation=allocation(),
                run=run(),
                validation=validation(
                    status="failed",
                    workspace_stable=False,
                    commands=(failed_command,),
                ),
            )
        )
        self.assertEqual(
            (validation_failed.phase, validation_failed.next_action),
            ("blocked", "repair_validation"),
        )

        publication_failed = assess_lifecycle(
            evidence(
                run=run(),
                validation=validation(),
                publication=publication(
                    status="failed",
                    failed_phase="push",
                    error="push failed",
                    last_successful_phase="commit",
                    pr_url=None,
                ),
            )
        )
        self.assertEqual(
            (publication_failed.phase, publication_failed.next_action),
            ("blocked", "resume_publication"),
        )

    def test_human_gates_remain_independent_of_automated_green(self) -> None:
        base = evidence(
            run=run(),
            validation=validation(),
            publication=publication(),
            pr=pr(merged=True),
        )

        pending = assess_lifecycle(replace(base, human_gates=(gate("PENDING"),)))
        self.assertEqual(
            (pending.phase, pending.next_action),
            ("awaiting_human", "await_human_gate"),
        )
        self.assertEqual(pending.blockers[0].code, "human_gate_pending")

        failed = assess_lifecycle(replace(base, human_gates=(gate("FAILED"),)))
        self.assertEqual(
            (failed.phase, failed.next_action),
            ("blocked", "remediate_human_gate"),
        )
        self.assertEqual(failed.blockers[0].code, "human_gate_failed")

        stale = assess_lifecycle(
            replace(
                base,
                human_gates=(
                    gate("PASSED", freshness_boundary="HEAD stale-sha"),
                ),
            )
        )
        self.assertEqual(
            (stale.phase, stale.next_action),
            ("awaiting_human", "await_human_gate"),
        )
        self.assertEqual(stale.blockers[0].code, "human_gate_stale")

        passed = assess_lifecycle(replace(base, human_gates=(gate("PASSED"),)))
        self.assertEqual(
            (passed.phase, passed.next_action),
            ("merged", "reconcile_post_publication"),
        )

    def test_continuation_is_freshness_bound_and_exposes_one_next_action(self) -> None:
        assessment = assess_lifecycle(
            evidence(
                allocation=allocation(),
                run=run(),
                validation=validation(),
            )
        )
        payload = assessment.to_dict()
        continuation = payload["continuation"]
        self.assertEqual(continuation["repository"], REPO)
        self.assertEqual(continuation["baseBranch"], "master")
        self.assertEqual(continuation["branch"], BRANCH)
        self.assertEqual(continuation["headSha"], HEAD)
        self.assertEqual(
            continuation["nextAction"],
            assessment.next_action,
        )
        self.assertIn("Re-check repository HEAD", continuation["freshnessInstruction"])
        self.assertIn("read-only projection", continuation["authorityBoundary"])


class HumanGateContractTests(unittest.TestCase):
    def test_waiver_requires_rationale(self) -> None:
        raw = gate("WAIVED", rationale=None).to_dict(head_sha=HEAD)
        raw.pop("fresh", None)
        with self.assertRaises(LifecycleError):
            HumanAsyncGate.from_dict(raw)

    def test_gate_file_is_read_only_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "gates.json"
            path.write_text(
                """[
  {
    "gateId": "HAG-001",
    "subject": "smoke",
    "triggerEvidence": "preview",
    "expectedObservation": "works",
    "approver": "owner",
    "status": "PENDING",
    "freshnessBoundary": "HEAD aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "nextAction": "record result",
    "required": true
  }
]
""",
                encoding="utf-8",
            )
            before = path.read_bytes()
            gates = _load_human_gates(path)
            after = path.read_bytes()
            self.assertEqual(len(gates), 1)
            self.assertEqual(gates[0].status, "PENDING")
            self.assertEqual(before, after)


class ReadOnlyAdapterTests(unittest.TestCase):
    @patch("engineering_graph.lifecycle.subprocess.run")
    def test_pr_inspection_uses_argv_shell_false(self, subprocess_run) -> None:
        subprocess_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"number":1,"state":"OPEN","mergedAt":null,'
                '"mergeCommit":null,'
                '"url":"https://github.com/example/repo/pull/1",'
                '"baseRefName":"master","headRefName":"exec/spec-018-t008"}'
            ),
            stderr="",
        )
        settings = MagicMock(repo_root=Path("/tmp/repo"))
        snapshot = _inspect_pr_read_only(settings, publication())
        self.assertEqual(snapshot.state, "OPEN")
        args, kwargs = subprocess_run.call_args
        self.assertEqual(args[0][:3], ["gh", "pr", "view"])
        self.assertFalse(kwargs["shell"])

    @patch("engineering_graph.lifecycle._load_human_gates")
    @patch("engineering_graph.lifecycle._inspect_pr_read_only")
    @patch("engineering_graph.lifecycle.load_receipt")
    @patch("engineering_graph.lifecycle.list_publication_records")
    @patch("engineering_graph.lifecycle.list_validation_records")
    @patch("engineering_graph.lifecycle.list_supervisor_jobs")
    @patch("engineering_graph.lifecycle.latest_run")
    @patch("engineering_graph.lifecycle.load_runner_registry")
    @patch("engineering_graph.lifecycle.registry_path")
    @patch("engineering_graph.lifecycle.active_lease")
    @patch("engineering_graph.lifecycle.load_registry")
    @patch("engineering_graph.lifecycle.current_git_revision")
    def test_collection_only_reads_existing_evidence(
        self,
        current_revision,
        load_lease_registry,
        active_lease_mock,
        registry_path_mock,
        load_runner_registry_mock,
        latest_run_mock,
        supervisor_jobs,
        validations,
        publications,
        load_receipt_mock,
        inspect_pr,
        load_gates,
    ) -> None:
        current_revision.return_value = HEAD
        load_lease_registry.return_value = MagicMock()
        active_lease_mock.return_value = allocation()
        registry_path_mock.return_value = Path("/tmp/execution/runs/registry.json")
        load_runner_registry_mock.return_value = MagicMock()
        latest_run_mock.return_value = run()
        supervisor_jobs.return_value = ()
        validations.return_value = (validation(),)
        publications.return_value = (publication(),)
        load_receipt_mock.return_value = None
        inspect_pr.return_value = pr()
        load_gates.return_value = ()

        settings = MagicMock(
            repository_id=REPO,
            repo_root=Path("/tmp/repo"),
            tool_root=Path("/tmp/tool"),
        )
        result = collect_lifecycle_evidence(settings, TASK)

        self.assertEqual(result.allocation, allocation())
        self.assertEqual(result.run, run())
        self.assertEqual(result.validation, validation())
        self.assertEqual(result.publication, publication())
        self.assertEqual(result.pr, pr())
        load_receipt_mock.assert_called_once()
        inspect_pr.assert_called_once()


if __name__ == "__main__":
    unittest.main()
