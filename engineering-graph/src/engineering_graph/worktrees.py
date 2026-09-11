from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Sequence


class GitWorktreeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class WorktreeDescriptor:
    path: Path
    head: str | None
    branch: str | None
    bare: bool = False
    detached: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "head": self.head,
            "branch": self.branch,
            "bare": self.bare,
            "detached": self.detached,
        }


def normalize_task_component(task_id: str) -> str:
    value = re.sub(r"[^a-z0-9._-]+", "-", task_id.strip().lower())
    value = re.sub(r"[-_.]{2,}", "-", value).strip("-._")
    if not value:
        raise ValueError("Task ID cannot be normalized into a worktree component")
    return value


def branch_name_for_task(task_id: str) -> str:
    return f"exec/{normalize_task_component(task_id)}"


def worktree_path_for_task(root: Path, task_id: str) -> Path:
    return (root / "worktrees" / normalize_task_component(task_id)).resolve()


def _run_git(
    repo_root: Path,
    *args: str,
    check: bool = True,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd or repo_root,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        rendered = " ".join(["git", *args])
        detail = result.stderr.strip() or result.stdout.strip() or f"exit={result.returncode}"
        raise GitWorktreeError(f"{rendered} failed: {detail}")
    return result


def list_worktrees(repo_root: Path) -> tuple[WorktreeDescriptor, ...]:
    result = _run_git(repo_root, "worktree", "list", "--porcelain")
    descriptors: list[WorktreeDescriptor] = []
    current: dict[str, object] = {}

    def flush() -> None:
        if not current:
            return
        path = current.get("path")
        if not isinstance(path, Path):
            raise GitWorktreeError("Malformed git worktree porcelain output: missing worktree path")
        descriptors.append(
            WorktreeDescriptor(
                path=path.resolve(),
                head=str(current["head"]) if current.get("head") else None,
                branch=str(current["branch"]) if current.get("branch") else None,
                bare=bool(current.get("bare")),
                detached=bool(current.get("detached")),
            )
        )
        current.clear()

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            if current:
                flush()
            current["path"] = Path(value)
        elif key == "HEAD":
            current["head"] = value
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
        elif key == "bare":
            current["bare"] = True
        elif key == "detached":
            current["detached"] = True
    flush()
    return tuple(descriptors)


def branch_exists(repo_root: Path, branch: str) -> bool:
    result = _run_git(
        repo_root,
        "show-ref",
        "--verify",
        "--quiet",
        f"refs/heads/{branch}",
        check=False,
    )
    return result.returncode == 0


def branch_head(repo_root: Path, branch: str) -> str | None:
    result = _run_git(repo_root, "rev-parse", f"refs/heads/{branch}", check=False)
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def find_worktree(
    worktrees: Sequence[WorktreeDescriptor],
    *,
    path: Path | None = None,
    branch: str | None = None,
) -> WorktreeDescriptor | None:
    resolved = path.resolve() if path is not None else None
    for descriptor in worktrees:
        if resolved is not None and descriptor.path == resolved:
            return descriptor
        if branch is not None and descriptor.branch == branch:
            return descriptor
    return None


def ensure_worktree(
    repo_root: Path,
    *,
    path: Path,
    branch: str,
    source_revision: str,
) -> tuple[WorktreeDescriptor, bool]:
    path = path.resolve()
    worktrees = list_worktrees(repo_root)
    by_path = find_worktree(worktrees, path=path)
    by_branch = find_worktree(worktrees, branch=branch)

    if by_path is not None:
        if by_path.branch != branch:
            raise GitWorktreeError(
                f"Worktree path {path} is already registered for branch {by_path.branch or 'detached'}"
            )
        return by_path, False

    if by_branch is not None:
        raise GitWorktreeError(
            f"Branch {branch} is already checked out at {by_branch.path}; refusing duplicate allocation"
        )

    if path.exists():
        raise GitWorktreeError(f"Worktree path already exists outside Git worktree registry: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    if branch_exists(repo_root, branch):
        _run_git(repo_root, "worktree", "add", str(path), branch)
    else:
        _run_git(repo_root, "worktree", "add", str(path), "-b", branch, source_revision)

    descriptor = find_worktree(list_worktrees(repo_root), path=path)
    if descriptor is None:
        raise GitWorktreeError(f"Git did not register expected worktree: {path}")
    if descriptor.branch != branch:
        raise GitWorktreeError(
            f"Registered worktree branch mismatch: expected={branch} actual={descriptor.branch}"
        )
    return descriptor, True


def is_worktree_dirty(path: Path) -> bool:
    result = _run_git(path, "status", "--porcelain", cwd=path)
    return bool(result.stdout.strip())


def remove_worktree(repo_root: Path, path: Path, *, force: bool = False) -> None:
    path = path.resolve()
    descriptor = find_worktree(list_worktrees(repo_root), path=path)
    if descriptor is None:
        if path.exists():
            raise GitWorktreeError(f"Path exists but is not a registered Git worktree: {path}")
        return

    if is_worktree_dirty(path) and not force:
        raise GitWorktreeError(
            f"Worktree {path} has uncommitted/untracked changes; use force only when destructive cleanup is intended"
        )

    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    args.append(str(path))
    _run_git(repo_root, *args)


def current_revision(repo_root: Path) -> str:
    result = _run_git(repo_root, "rev-parse", "HEAD")
    revision = result.stdout.strip()
    if not revision:
        raise GitWorktreeError("Unable to resolve current Git HEAD")
    return revision
