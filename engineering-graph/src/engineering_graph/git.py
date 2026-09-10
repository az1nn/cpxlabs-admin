from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
from typing import Iterable

from .model import GraphEdge, GraphModel, GraphNode
from .parser import (
    canonical_spec_id,
    canonical_task_id,
    code_kind,
    is_test_path,
    normalize_path,
    test_kind,
)

_MERGE_PR_RE = re.compile(r"Merge pull request #(?P<number>\d+)", re.IGNORECASE)
_SPEC_PATH_RE = re.compile(r"specs/(?P<feature>\d{3}-[a-z0-9-]+)", re.IGNORECASE)
_CANONICAL_TASK_RE = re.compile(r"\b(?P<spec>SPEC-\d{3}-[A-Z0-9-]+):(?P<task>T\d{3})\b", re.IGNORECASE)
_LOCAL_TASK_RE = re.compile(r"\bT(?P<number>\d{3})\b", re.IGNORECASE)
_TASK_RANGE_RE = re.compile(r"\bT(?P<start>\d{3})\s*[–—-]\s*T?(?P<end>\d{3})\b", re.IGNORECASE)


def _git(repo_root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=check,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def current_revision(repo_root: Path) -> str:
    return _git(repo_root, "rev-parse", "HEAD")


def _changed_paths(repo_root: Path, base: str, head: str) -> list[str]:
    try:
        output = _git(repo_root, "diff", "--name-only", f"{base}...{head}")
    except subprocess.CalledProcessError:
        try:
            output = _git(repo_root, "diff", "--name-only", base, head)
        except subprocess.CalledProcessError:
            return []
    return sorted({normalize_path(line) for line in output.splitlines() if line.strip()})


def _ensure_path_node(model: GraphModel, repo_root: Path, path: str) -> tuple[str, str]:
    normalized = normalize_path(path)
    exists = (repo_root / normalized).exists()
    if is_test_path(normalized):
        model.add_node(
            GraphNode(
                "Test",
                normalized,
                {"path": normalized, "kind": test_kind(normalized), "exists": exists},
            )
        )
        return "Test", normalized
    model.add_node(
        GraphNode(
            "CodeArtifact",
            normalized,
            {"path": normalized, "kind": code_kind(normalized), "exists": exists},
        )
    )
    return "CodeArtifact", normalized


def _task_ids_from_text(text: str, model: GraphModel) -> set[str]:
    task_ids: set[str] = set()
    for match in _CANONICAL_TASK_RE.finditer(text):
        task_ids.add(f"{match.group('spec').upper()}:{match.group('task').upper()}")

    spec_match = _SPEC_PATH_RE.search(text)
    if not spec_match:
        return task_ids

    spec_id = canonical_spec_id(spec_match.group("feature").lower())
    for match in _LOCAL_TASK_RE.finditer(text):
        candidate = canonical_task_id(spec_id, f"T{match.group('number')}")
        if model.node("Task", candidate):
            task_ids.add(candidate)

    for match in _TASK_RANGE_RE.finditer(text):
        start = int(match.group("start"))
        end = int(match.group("end"))
        if end < start or end - start > 500:
            continue
        for number in range(start, end + 1):
            candidate = canonical_task_id(spec_id, f"T{number:03d}")
            if model.node("Task", candidate):
                task_ids.add(candidate)
    return task_ids


def _link_pr(
    model: GraphModel,
    repo_root: Path,
    repository_id: str,
    number: int,
    title: str,
    state: str,
    source: str,
    body: str,
    changed_paths: Iterable[str],
    url: str | None = None,
    head_sha: str | None = None,
    base_sha: str | None = None,
) -> None:
    canonical_id = f"{repository_id}#{number}"
    model.add_node(
        GraphNode(
            "PullRequest",
            canonical_id,
            {
                "number": number,
                "title": title,
                "state": state,
                "url": url,
                "headSha": head_sha,
                "baseSha": base_sha,
                "source": source,
            },
        )
    )

    for path in changed_paths:
        label, path_id = _ensure_path_node(model, repo_root, path)
        model.add_edge(
            GraphEdge(
                "PullRequest",
                canonical_id,
                "CHANGES",
                label,
                path_id,
                {"provenance": source},
            )
        )

    for task_id in sorted(_task_ids_from_text(f"{title}\n{body}", model)):
        model.add_edge(
            GraphEdge(
                "PullRequest",
                canonical_id,
                "IMPLEMENTS",
                "Task",
                task_id,
                {"provenance": source},
            )
        )


def ingest_merged_pull_requests(
    model: GraphModel,
    repo_root: Path,
    repository_id: str,
    limit: int = 200,
) -> None:
    try:
        output = _git(
            repo_root,
            "log",
            "--merges",
            f"--max-count={limit}",
            "--pretty=format:%H%x1f%s%x1f%b%x1e",
        )
    except subprocess.CalledProcessError:
        return

    for record in output.split("\x1e"):
        if not record.strip():
            continue
        parts = record.strip().split("\x1f", 2)
        if len(parts) != 3:
            continue
        sha, subject, body = parts
        match = _MERGE_PR_RE.search(subject)
        if not match:
            continue
        try:
            parents = _git(repo_root, "rev-list", "--parents", "-n", "1", sha).split()
        except subprocess.CalledProcessError:
            parents = []
        changed = _changed_paths(repo_root, parents[1], sha) if len(parents) > 1 else []
        title = next((line.strip() for line in body.splitlines() if line.strip()), subject)
        _link_pr(
            model,
            repo_root,
            repository_id,
            int(match.group("number")),
            title,
            "merged",
            "git",
            body,
            changed,
            head_sha=sha,
            base_sha=parents[1] if len(parents) > 1 else None,
        )


def ingest_github_event(
    model: GraphModel,
    repo_root: Path,
    repository_id: str,
    event_path: Path | None,
) -> None:
    if event_path is None or not event_path.exists():
        return
    try:
        payload = json.loads(event_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    pull_request = payload.get("pull_request")
    if not isinstance(pull_request, dict):
        return

    number = payload.get("number") or pull_request.get("number")
    if not isinstance(number, int):
        return
    head = pull_request.get("head", {})
    base = pull_request.get("base", {})
    head_sha = head.get("sha") if isinstance(head, dict) else None
    base_sha = base.get("sha") if isinstance(base, dict) else None
    changed = (
        _changed_paths(repo_root, str(base_sha), str(head_sha))
        if isinstance(head_sha, str) and isinstance(base_sha, str)
        else []
    )
    state = "merged" if pull_request.get("merged") else str(pull_request.get("state", "open"))
    _link_pr(
        model,
        repo_root,
        repository_id,
        number,
        str(pull_request.get("title", f"PR #{number}")),
        state,
        "github_event",
        str(pull_request.get("body") or ""),
        changed,
        url=str(pull_request.get("html_url") or "") or None,
        head_sha=str(head_sha) if head_sha else None,
        base_sha=str(base_sha) if base_sha else None,
    )
