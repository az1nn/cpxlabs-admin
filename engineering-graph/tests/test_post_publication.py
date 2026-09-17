from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from engineering_graph.post_publication import (
    CommandResult,
    PostPublicationError,
    PostPublicationReceipt,
    ReconciliationResult,
    _canonical_task_completed,
    _inspect_pr,
    _merge_reachable,
    finalize_post_publication,
    reconcile_post_publication,
    validate_receipt,
)
from engineering_graph.publisher import PublicationRecord

NOW = "2026-09-17T12:00:00+00:00"


def publication(**changes) -> PublicationRecord:
    values = dict(
        publication_id="pub-1",
        repository="example/repo",
        task_id="SPEC-016-GIT-PUBLISHER:T010",
        spec_id="SPEC-016-GIT-PUBLISHER",
        validation_id="val-1",
        run_id="run-1",
        source_revision="source-sha",
        workspace_revision="workspace-sha",
        workspace_fingerprint="fingerprint",
        branch="exec/spec-016-t010",
        base_branch="master",
        worktree_path="/tmp/worktree",
        commit_message="feat: task",
        pr_title="feat: task",
        pr_body="body",
        status="pr_opened",
        created_at=NOW,
        updated_at=NOW,
        last_successful_phase="pr",
        commit_sha="commit-sha",
        pr_url="https://github.com/example/repo/pull/9",
        finished_at=NOW,
    )
    values.update(changes)
    return PublicationRecord(**values)


def receipt(**changes) -> PostPublicationReceipt:
    values = dict(
        receipt_id="post-pub-1",
        repository="example/repo",
        publication_id="pub-1",
        validation_id="val-1",
        task_id="SPEC-016-GIT-PUBLISHER:T010",
        spec_id="SPEC-016-GIT-PUBLISHER",
        branch="exec/spec-016-t010",
        base_branch="master",
        worktree_path="/tmp/worktree",
        pr_url="https://github.com/example/repo/pull/9",
        pr_number=9,
        merge_commit_sha="merge-sha",
        base_revision="base-sha",
        canonical_task_path="specs/016-git-publisher/tasks.md",
        canonical_task_completed=True,
        lease_released=False,
        worktree_removed=False,
        status="reconciled",
        created_at=NOW,
        updated_at=NOW,
    )
    values.update(changes)
    return PostPublicationReceipt(**values)


def result(**changes) -> ReconciliationResult:
    values = dict(
        repository="example/repo",
        publication_id="pub-1",
        validation_id="val-1",
        task_id="SPEC-016-GIT-PUBLISHER:T010",
        spec_id="SPEC-016-GIT-PUBLISHER",
        branch="exec/spec-016-t010",
        base_branch="master",
        worktree_path="/tmp/worktree",
        pr_url="https://github.com/example/repo/pull/9",
        pr_number=9,
        pr_merged=True,
        merge_commit_sha="merge-sha",
        base_revision="base-sha",
        merge_reachable=True,
        canonical_task_path="specs/016-git-publisher/tasks.md",
        canonical_task_completed=True,
        lease_active=True,
        worktree_registered=True,
        worktree_dirty=False,
        already_finalized=False,
        finalizable=True,
        blockers=(),
    )
    values.update(changes)
    return ReconciliationResult(**values)


class PostPublicationContractTests(unittest.TestCase):
    def test_receipt_invariants(self) -> None:
        validate_receipt(receipt())
        validate_receipt(receipt(status="finalized", lease_released=True, finished_at=NOW))
        with self.assertRaises(PostPublicationError):
            validate_receipt(receipt(status="finalized", lease_released=False))
        with self.assertRaises(PostPublicationError):
            validate_receipt(receipt(status="blocked", block_reason=None))

    @patch("engineering_graph.post_publication._checked")
    def test_pr_inspection_requires_publication_identity(self, checked) -> None:
        checked.return_value = CommandResult(
            ("gh",),
            0,
            '{"number":9,"state":"MERGED","mergedAt":"now","mergeCommit":{"oid":"merge-sha"},"url":"https://github.com/example/repo/pull/9","baseRefName":"master","headRefName":"exec/spec-016-t010"}',
            "",
        )
        settings = MagicMock(repo_root=Path("/tmp/repo"))
        payload = _inspect_pr(settings, publication())
        self.assertEqual(payload["number"], 9)
        args = checked.call_args.args[1]
        self.assertEqual(args[:3], ("gh", "pr", "view"))

        checked.return_value = replace(checked.return_value, stdout=checked.return_value.stdout.replace("pull/9", "pull/10"))
        with self.assertRaises(PostPublicationError):
            _inspect_pr(settings, publication())

    @patch("engineering_graph.post_publication._run_command")
    def test_merge_reachability_is_fail_closed(self, run) -> None:
        settings = MagicMock(repo_root=Path("/tmp/repo"))
        run.return_value = CommandResult(("git",), 0, "", "")
        self.assertTrue(_merge_reachable(settings, "merge", "origin/master"))
        run.return_value = CommandResult(("git",), 1, "", "")
        self.assertFalse(_merge_reachable(settings, "merge", "origin/master"))
        run.return_value = CommandResult(("git",), 128, "", "fatal")
        with self.assertRaises(PostPublicationError):
            _merge_reachable(settings, "merge", "origin/master")

    @patch("engineering_graph.post_publication._checked")
    @patch("engineering_graph.post_publication._task_path")
    def test_canonical_task_must_be_unique_and_checked(self, task_path, checked) -> None:
        task_path.return_value = "specs/016-git-publisher/tasks.md"
        settings = MagicMock(repo_root=Path("/tmp/repo"))
        checked.return_value = CommandResult(("git",), 0, "- [x] T010 Done\n", "")
        path, complete = _canonical_task_completed(
            settings,
            base_ref="origin/master",
            spec_id="SPEC-016-GIT-PUBLISHER",
            task_id="SPEC-016-GIT-PUBLISHER:T010",
        )
        self.assertTrue(complete)
        self.assertEqual(path, "specs/016-git-publisher/tasks.md")

        checked.return_value = CommandResult(("git",), 0, "- [ ] T010 Pending\n", "")
        _, complete = _canonical_task_completed(
            settings,
            base_ref="origin/master",
            spec_id="SPEC-016-GIT-PUBLISHER",
            task_id="SPEC-016-GIT-PUBLISHER:T010",
        )
        self.assertFalse(complete)

        checked.return_value = CommandResult(("git",), 0, "- [x] T010 A\n- [x] T010 B\n", "")
        with self.assertRaises(PostPublicationError):
            _canonical_task_completed(
                settings,
                base_ref="origin/master",
                spec_id="SPEC-016-GIT-PUBLISHER",
                task_id="SPEC-016-GIT-PUBLISHER:T010",
            )


class PostPublicationLifecycleTests(unittest.TestCase):
    @patch("engineering_graph.post_publication.is_worktree_dirty")
    @patch("engineering_graph.post_publication.find_worktree")
    @patch("engineering_graph.post_publication.list_worktrees")
    @patch("engineering_graph.post_publication._matching_lease")
    @patch("engineering_graph.post_publication._canonical_task_completed")
    @patch("engineering_graph.post_publication._merge_reachable")
    @patch("engineering_graph.post_publication._refresh_base")
    @patch("engineering_graph.post_publication._inspect_pr")
    @patch("engineering_graph.post_publication.load_receipt")
    @patch("engineering_graph.post_publication.load_publication_record")
    def test_open_pr_blocks_finalization(
        self,
        load_publication,
        load_receipt,
        inspect_pr,
        refresh_base,
        merge_reachable,
        canonical_task,
        matching_lease,
        list_worktrees_mock,
        find_worktree_mock,
        dirty,
    ) -> None:
        load_publication.return_value = publication()
        load_receipt.return_value = None
        inspect_pr.return_value = {
            "number": 9,
            "state": "OPEN",
            "mergedAt": None,
            "mergeCommit": None,
            "url": publication().pr_url,
            "baseRefName": "master",
            "headRefName": publication().branch,
        }
        matching_lease.return_value = MagicMock()
        list_worktrees_mock.return_value = ()
        find_worktree_mock.return_value = None
        settings = MagicMock(repository_id="example/repo", repo_root=Path("/tmp/repo"))
        reconciled = reconcile_post_publication(settings, "pub-1")
        self.assertFalse(reconciled.finalizable)
        self.assertIn("pull request is not merged", reconciled.blockers)
        refresh_base.assert_not_called()
        canonical_task.assert_not_called()

    @patch("engineering_graph.post_publication.is_worktree_dirty")
    @patch("engineering_graph.post_publication.find_worktree")
    @patch("engineering_graph.post_publication.list_worktrees")
    @patch("engineering_graph.post_publication._matching_lease")
    @patch("engineering_graph.post_publication._canonical_task_completed")
    @patch("engineering_graph.post_publication._merge_reachable")
    @patch("engineering_graph.post_publication._refresh_base")
    @patch("engineering_graph.post_publication._inspect_pr")
    @patch("engineering_graph.post_publication.load_receipt")
    @patch("engineering_graph.post_publication.load_publication_record")
    def test_incomplete_canonical_task_blocks_cleanup(
        self,
        load_publication,
        load_receipt,
        inspect_pr,
        refresh_base,
        merge_reachable,
        canonical_task,
        matching_lease,
        list_worktrees_mock,
        find_worktree_mock,
        dirty,
    ) -> None:
        record = publication()
        load_publication.return_value = record
        load_receipt.return_value = None
        inspect_pr.return_value = {
            "number": 9,
            "state": "MERGED",
            "mergedAt": NOW,
            "mergeCommit": {"oid": "merge-sha"},
            "url": record.pr_url,
            "baseRefName": "master",
            "headRefName": record.branch,
        }
        refresh_base.return_value = ("refs/remotes/origin/master", "base-sha")
        merge_reachable.return_value = True
        canonical_task.return_value = ("specs/016-git-publisher/tasks.md", False)
        matching_lease.return_value = MagicMock()
        list_worktrees_mock.return_value = ()
        find_worktree_mock.return_value = None
        settings = MagicMock(repository_id="example/repo", repo_root=Path("/tmp/repo"))
        reconciled = reconcile_post_publication(settings, "pub-1")
        self.assertFalse(reconciled.finalizable)
        self.assertIn("canonical Task is not complete in merged base", reconciled.blockers)

    @patch("engineering_graph.post_publication.save_receipt")
    @patch("engineering_graph.post_publication.release_lease")
    @patch("engineering_graph.post_publication.reconcile_post_publication")
    @patch("engineering_graph.post_publication.load_receipt")
    def test_finalize_requires_explicit_release_and_is_idempotent(
        self,
        load_receipt,
        reconcile,
        release,
        save,
    ) -> None:
        settings = MagicMock(repository_id="example/repo", repo_root=Path("/tmp/repo"))
        load_receipt.return_value = None
        reconcile.return_value = result(worktree_registered=False)
        with self.assertRaises(PostPublicationError):
            finalize_post_publication(settings, "pub-1", release=False)

        finalized = finalize_post_publication(settings, "pub-1", release=True)
        self.assertEqual(finalized.status, "finalized")
        self.assertTrue(finalized.lease_released)
        release.assert_called_once()

        load_receipt.return_value = finalized
        again = finalize_post_publication(settings, "pub-1", release=True)
        self.assertEqual(again, finalized)
        self.assertEqual(release.call_count, 1)

    @patch("engineering_graph.post_publication.save_receipt")
    @patch("engineering_graph.post_publication.is_worktree_dirty")
    @patch("engineering_graph.post_publication.find_worktree")
    @patch("engineering_graph.post_publication.list_worktrees")
    @patch("engineering_graph.post_publication.release_lease")
    @patch("engineering_graph.post_publication.reconcile_post_publication")
    @patch("engineering_graph.post_publication.load_receipt")
    def test_dirty_worktree_is_never_force_removed(
        self,
        load_receipt,
        reconcile,
        release,
        list_worktrees_mock,
        find_worktree_mock,
        dirty,
        save,
    ) -> None:
        settings = MagicMock(repository_id="example/repo", repo_root=Path("/tmp/repo"))
        load_receipt.return_value = None
        reconcile.return_value = result()
        descriptor = MagicMock()
        list_worktrees_mock.return_value = (descriptor,)
        find_worktree_mock.return_value = descriptor
        dirty.return_value = True
        with self.assertRaises(PostPublicationError):
            finalize_post_publication(settings, "pub-1", release=True, remove=True)
        release.assert_called_once()
        saved_receipts = [call.args[1] for call in save.call_args_list]
        self.assertTrue(any(item.status == "blocked" for item in saved_receipts))
        self.assertTrue(any(item.lease_released for item in saved_receipts))


if __name__ == "__main__":
    unittest.main()
