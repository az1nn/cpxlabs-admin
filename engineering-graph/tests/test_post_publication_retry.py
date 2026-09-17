from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from engineering_graph.post_publication import (
    PostPublicationReceipt,
    ReconciliationResult,
    finalize_post_publication,
)

NOW = "2026-09-17T12:00:00+00:00"


class PostPublicationRetryTests(unittest.TestCase):
    @patch("engineering_graph.post_publication.save_receipt")
    @patch("engineering_graph.post_publication.remove_worktree")
    @patch("engineering_graph.post_publication.is_worktree_dirty")
    @patch("engineering_graph.post_publication.find_worktree")
    @patch("engineering_graph.post_publication.list_worktrees")
    @patch("engineering_graph.post_publication.reconcile_post_publication")
    @patch("engineering_graph.post_publication.load_receipt")
    def test_retry_can_remove_worktree_after_lease_was_already_released(
        self,
        load_receipt,
        reconcile,
        list_worktrees_mock,
        find_worktree_mock,
        dirty,
        remove,
        save,
    ) -> None:
        existing = PostPublicationReceipt(
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
            lease_released=True,
            worktree_removed=False,
            status="blocked",
            block_reason="worktree is dirty; V9 never force-removes dirty worktrees",
            created_at=NOW,
            updated_at=NOW,
        )
        load_receipt.return_value = existing
        reconcile.return_value = ReconciliationResult(
            repository="example/repo",
            publication_id="pub-1",
            validation_id="val-1",
            task_id=existing.task_id,
            spec_id=existing.spec_id,
            branch=existing.branch,
            base_branch="master",
            worktree_path=existing.worktree_path,
            pr_url=existing.pr_url,
            pr_number=9,
            pr_merged=True,
            merge_commit_sha="merge-sha",
            base_revision="base-sha",
            merge_reachable=True,
            canonical_task_path=existing.canonical_task_path,
            canonical_task_completed=True,
            lease_active=False,
            worktree_registered=True,
            worktree_dirty=False,
            already_finalized=False,
            finalizable=False,
            blockers=("matching active lease is missing",),
        )
        descriptor = MagicMock()
        list_worktrees_mock.return_value = (descriptor,)
        find_worktree_mock.return_value = descriptor
        dirty.return_value = False
        settings = MagicMock(repository_id="example/repo", repo_root=Path("/tmp/repo"))

        updated = finalize_post_publication(
            settings,
            "pub-1",
            release=True,
            remove=True,
        )

        self.assertTrue(updated.lease_released)
        self.assertTrue(updated.worktree_removed)
        self.assertEqual(updated.status, "finalized")
        remove.assert_called_once()
        self.assertTrue(save.called)


if __name__ == "__main__":
    unittest.main()
