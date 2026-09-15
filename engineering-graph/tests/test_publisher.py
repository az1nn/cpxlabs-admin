from __future__ import annotations

from dataclasses import replace
import unittest
from unittest.mock import MagicMock, patch

from engineering_graph.execution import ExecutionAllocation
from engineering_graph.publisher import (
    CommandResult,
    PublicationError,
    PublicationRecord,
    _assert_validation_matches_allocation,
    _create_pr,
    _push,
    _remote_repository,
    resume_publication,
    validate_publication_record,
)
from engineering_graph.validation import ValidationRecord

NOW = "2026-09-15T00:00:00+00:00"


def publication(**changes) -> PublicationRecord:
    values = dict(
        publication_id="pub-1",
        repository="example/repo",
        task_id="SPEC-016-GIT-PUBLISHER:T010",
        spec_id="SPEC-016-GIT-PUBLISHER",
        validation_id="val-1",
        run_id="run-1",
        source_revision="base-sha",
        workspace_revision="workspace-sha",
        workspace_fingerprint="fingerprint",
        branch="exec/spec-016-t010",
        base_branch="master",
        worktree_path="/tmp/worktree",
        commit_message="feat: publish task",
        pr_title="feat: publish task",
        pr_body="body",
        status="started",
        created_at=NOW,
        updated_at=NOW,
    )
    values.update(changes)
    return PublicationRecord(**values)


def allocation() -> ExecutionAllocation:
    return ExecutionAllocation(
        repository="example/repo",
        task_id="SPEC-016-GIT-PUBLISHER:T010",
        spec_id="SPEC-016-GIT-PUBLISHER",
        source_revision="base-sha",
        agent="codex",
        branch="exec/spec-016-t010",
        worktree_path="/tmp/worktree",
        context_path="/tmp/context.json",
        handoff_path="/tmp/handoff.md",
        lease_status="active",
        validation_commands=("python -m unittest",),
        created_at=NOW,
        updated_at=NOW,
    )


def validation(**changes) -> ValidationRecord:
    values = dict(
        validation_id="val-1",
        repository="example/repo",
        task_id="SPEC-016-GIT-PUBLISHER:T010",
        spec_id="SPEC-016-GIT-PUBLISHER",
        source_revision="base-sha",
        run_id="run-1",
        branch="exec/spec-016-t010",
        worktree_path="/tmp/worktree",
        workspace_revision="workspace-sha",
        workspace_fingerprint_before="fingerprint",
        workspace_fingerprint_after="fingerprint",
        workspace_stable=True,
        status="passed",
        commands=(),
        created_at=NOW,
        finished_at=NOW,
    )
    values.update(changes)
    return ValidationRecord(**values)


class GitPublisherTests(unittest.TestCase):
    def test_remote_repository_accepts_https_and_ssh(self) -> None:
        self.assertEqual(_remote_repository("https://github.com/example/repo.git"), "example/repo")
        self.assertEqual(_remote_repository("git@github.com:example/repo.git"), "example/repo")
        with self.assertRaises(PublicationError):
            _remote_repository("https://gitlab.com/example/repo.git")

    def test_record_invariants_require_commit_and_pr_url(self) -> None:
        validate_publication_record(publication())
        with self.assertRaises(PublicationError):
            validate_publication_record(publication(status="committed"))
        opened = publication(
            status="pr_opened",
            last_successful_phase="pr",
            commit_sha="commit-sha",
            pr_url="https://github.com/example/repo/pull/1",
            finished_at=NOW,
        )
        validate_publication_record(opened)

    def test_validation_must_match_active_allocation(self) -> None:
        _assert_validation_matches_allocation(validation(), allocation())
        with self.assertRaises(PublicationError):
            _assert_validation_matches_allocation(validation(branch="other"), allocation())
        with self.assertRaises(PublicationError):
            _assert_validation_matches_allocation(validation(status="failed"), allocation())

    @patch("engineering_graph.publisher.save_publication_record")
    @patch("engineering_graph.publisher._git")
    @patch("engineering_graph.publisher._assert_origin_repository")
    @patch("engineering_graph.publisher._assert_committed_workspace")
    def test_push_is_non_force_and_uses_allocation_branch(
        self,
        committed_check,
        origin_check,
        git,
        save,
    ) -> None:
        git.return_value = CommandResult(("git",), 0, "", "")
        settings = MagicMock(repository_id="example/repo")
        record = publication(
            status="committed",
            last_successful_phase="commit",
            commit_sha="commit-sha",
        )
        result = _push(settings, record, root_override=None)
        self.assertEqual(result.status, "pushed")
        args = git.call_args.args
        self.assertEqual(args[1:4], ("push", "--set-upstream", "origin"))
        self.assertEqual(args[4], "HEAD:refs/heads/exec/spec-016-t010")
        self.assertNotIn("--force", args)
        self.assertNotIn("--force-with-lease", args)
        save.assert_called()

    @patch("engineering_graph.publisher._checked")
    @patch("engineering_graph.publisher._existing_pr_url")
    def test_create_pr_reuses_existing_open_pr(self, existing, checked) -> None:
        existing.return_value = "https://github.com/example/repo/pull/7"
        record = publication(
            status="pushed",
            last_successful_phase="push",
            commit_sha="commit-sha",
        )
        self.assertEqual(_create_pr(record), "https://github.com/example/repo/pull/7")
        checked.assert_not_called()

    @patch("engineering_graph.publisher._open_pr")
    @patch("engineering_graph.publisher._push")
    @patch("engineering_graph.publisher._stage_and_commit")
    @patch("engineering_graph.publisher._assert_committed_workspace")
    @patch("engineering_graph.publisher._assert_resume_identity")
    @patch("engineering_graph.publisher.load_publication_record")
    @patch("engineering_graph.publisher._assert_binary")
    def test_resume_after_push_never_creates_duplicate_commit(
        self,
        binary,
        load,
        resume_identity,
        committed_check,
        stage_commit,
        push,
        open_pr,
    ) -> None:
        record = publication(
            status="failed",
            last_successful_phase="push",
            commit_sha="commit-sha",
            failed_phase="pr",
            error="network",
            finished_at=NOW,
        )
        opened = replace(
            record,
            status="pr_opened",
            last_successful_phase="pr",
            failed_phase=None,
            error=None,
            pr_url="https://github.com/example/repo/pull/8",
        )
        load.return_value = record
        open_pr.return_value = opened
        result = resume_publication(MagicMock(), record.publication_id)
        self.assertEqual(result.status, "pr_opened")
        stage_commit.assert_not_called()
        push.assert_not_called()
        open_pr.assert_called_once()


if __name__ == "__main__":
    unittest.main()
