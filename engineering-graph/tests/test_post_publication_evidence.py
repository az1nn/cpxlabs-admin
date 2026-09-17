from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from engineering_graph.post_publication import (
    PostPublicationError,
    PostPublicationReceipt,
    finalize_post_publication,
    load_receipt,
    reconcile_post_publication,
    save_receipt,
)
from engineering_graph.publisher import PublicationRecord

NOW = "2026-09-17T12:00:00+00:00"


def publication() -> PublicationRecord:
    return PublicationRecord(
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


def receipt() -> PostPublicationReceipt:
    return PostPublicationReceipt(
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


class PostPublicationEvidenceTests(unittest.TestCase):
    def test_receipt_roundtrip_and_malformed_json_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = MagicMock(repository_id="example/repo", tool_root=root, repo_root=root)
            expected = receipt()
            save_receipt(settings, expected, root_override=root)
            self.assertEqual(load_receipt(settings, "pub-1", root_override=root), expected)

            path = root / "post-publication" / "receipts" / "pub-1.json"
            path.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(PostPublicationError):
                load_receipt(settings, "pub-1", root_override=root)

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
    def test_merged_but_unreachable_pr_blocks_cleanup(
        self,
        load_publication,
        load_receipt_mock,
        inspect_pr,
        refresh_base,
        reachable,
        canonical,
        matching_lease,
        list_worktrees_mock,
        find_worktree_mock,
        dirty,
    ) -> None:
        record = publication()
        load_publication.return_value = record
        load_receipt_mock.return_value = None
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
        reachable.return_value = False
        matching_lease.return_value = MagicMock()
        list_worktrees_mock.return_value = ()
        find_worktree_mock.return_value = None
        settings = MagicMock(repository_id="example/repo", repo_root=Path("/tmp/repo"))

        result = reconcile_post_publication(settings, "pub-1")
        self.assertFalse(result.finalizable)
        self.assertIn("merge commit is not reachable from refreshed base", result.blockers)
        canonical.assert_not_called()

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
    def test_merged_reachable_canonical_complete_is_finalizable(
        self,
        load_publication,
        load_receipt_mock,
        inspect_pr,
        refresh_base,
        reachable,
        canonical,
        matching_lease,
        list_worktrees_mock,
        find_worktree_mock,
        dirty,
    ) -> None:
        record = publication()
        load_publication.return_value = record
        load_receipt_mock.return_value = None
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
        reachable.return_value = True
        canonical.return_value = ("specs/016-git-publisher/tasks.md", True)
        matching_lease.return_value = MagicMock()
        list_worktrees_mock.return_value = ()
        find_worktree_mock.return_value = None
        settings = MagicMock(repository_id="example/repo", repo_root=Path("/tmp/repo"))

        result = reconcile_post_publication(settings, "pub-1")
        self.assertTrue(result.finalizable)
        self.assertEqual(result.blockers, ())
        self.assertTrue(result.canonical_task_completed)
        self.assertTrue(result.merge_reachable)

    @patch("engineering_graph.post_publication.save_receipt")
    @patch("engineering_graph.post_publication.remove_worktree")
    @patch("engineering_graph.post_publication.is_worktree_dirty")
    @patch("engineering_graph.post_publication.find_worktree")
    @patch("engineering_graph.post_publication.list_worktrees")
    @patch("engineering_graph.post_publication.release_lease")
    @patch("engineering_graph.post_publication.reconcile_post_publication")
    @patch("engineering_graph.post_publication.load_receipt")
    def test_finalize_targets_only_publication_task_and_worktree(
        self,
        load_receipt_mock,
        reconcile,
        release,
        list_worktrees_mock,
        find_worktree_mock,
        dirty,
        remove,
        save,
    ) -> None:
        load_receipt_mock.return_value = None
        reconcile.return_value = MagicMock(
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
        descriptor = MagicMock()
        list_worktrees_mock.return_value = (descriptor,)
        find_worktree_mock.return_value = descriptor
        dirty.return_value = False
        settings = MagicMock(repository_id="example/repo", repo_root=Path("/tmp/repo"))

        finalized = finalize_post_publication(settings, "pub-1", release=True, remove=True)
        self.assertTrue(finalized.lease_released)
        self.assertTrue(finalized.worktree_removed)
        release.assert_called_once()
        self.assertEqual(release.call_args.kwargs["task_id"], "SPEC-016-GIT-PUBLISHER:T010")
        remove.assert_called_once_with(settings.repo_root, Path("/tmp/worktree"), force=False)


if __name__ == "__main__":
    unittest.main()
