from __future__ import annotations

from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from engineering_graph.worktrees import (
    GitWorktreeError,
    branch_name_for_task,
    current_revision,
    ensure_worktree,
    is_worktree_dirty,
    list_worktrees,
    normalize_task_component,
    remove_worktree,
    worktree_path_for_task,
)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def init_repo(root: Path) -> None:
    git(root, "init")
    git(root, "config", "user.email", "graph-tests@example.invalid")
    git(root, "config", "user.name", "Engineering Graph Tests")
    (root / "README.md").write_text("# fixture\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-m", "fixture")


class WorktreeTests(unittest.TestCase):
    def test_normalization_is_stable(self) -> None:
        self.assertEqual(
            normalize_task_component("SPEC-011-EXECUTION-GRAPH:T021"),
            "spec-011-execution-graph-t021",
        )
        self.assertEqual(
            branch_name_for_task("SPEC-011-EXECUTION-GRAPH:T021"),
            "exec/spec-011-execution-graph-t021",
        )

    def test_create_resume_and_remove_real_worktree(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            init_repo(root)
            execution_root = root / ".execution"
            task_id = "SPEC-011:T001"
            branch = branch_name_for_task(task_id)
            path = worktree_path_for_task(execution_root, task_id)
            revision = current_revision(root)

            descriptor, created = ensure_worktree(
                root,
                path=path,
                branch=branch,
                source_revision=revision,
            )
            self.assertTrue(created)
            self.assertEqual(descriptor.path, path.resolve())
            self.assertEqual(descriptor.branch, branch)
            self.assertTrue(path.exists())

            resumed, created_again = ensure_worktree(
                root,
                path=path,
                branch=branch,
                source_revision=revision,
            )
            self.assertFalse(created_again)
            self.assertEqual(resumed.path, path.resolve())

            remove_worktree(root, path)
            self.assertFalse(path.exists())
            self.assertNotIn(path.resolve(), {item.path for item in list_worktrees(root)})

    def test_dirty_worktree_requires_force(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            init_repo(root)
            task_id = "SPEC-011:T002"
            path = worktree_path_for_task(root / ".execution", task_id)
            ensure_worktree(
                root,
                path=path,
                branch=branch_name_for_task(task_id),
                source_revision=current_revision(root),
            )
            (path / "dirty.txt").write_text("user work\n", encoding="utf-8")
            self.assertTrue(is_worktree_dirty(path))
            with self.assertRaisesRegex(GitWorktreeError, "uncommitted/untracked"):
                remove_worktree(root, path)
            self.assertTrue(path.exists())
            remove_worktree(root, path, force=True)
            self.assertFalse(path.exists())

    def test_foreign_path_fails_closed(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            init_repo(root)
            task_id = "SPEC-011:T003"
            path = worktree_path_for_task(root / ".execution", task_id)
            path.mkdir(parents=True)
            with self.assertRaisesRegex(GitWorktreeError, "outside Git worktree registry"):
                ensure_worktree(
                    root,
                    path=path,
                    branch=branch_name_for_task(task_id),
                    source_revision=current_revision(root),
                )


if __name__ == "__main__":
    unittest.main()
