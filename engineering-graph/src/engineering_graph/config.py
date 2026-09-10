from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class Neo4jSettings:
    uri: str
    user: str
    password: str
    database: str


@dataclass(frozen=True, slots=True)
class ContextBudget:
    max_depth: int
    max_nodes: int


@dataclass(frozen=True, slots=True)
class GraphSettings:
    tool_root: Path
    repo_root: Path
    repository_id: str
    neo4j: Neo4jSettings
    context: ContextBudget
    validation_rules: dict[str, str]
    historical_spec_prefixes: tuple[str, ...]
    specs_glob: str
    tasks_name: str
    plans_name: str
    adr_glob: str
    prune_stale: bool


def _run_git(repo_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def discover_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    probe = _run_git(current, "rev-parse", "--show-toplevel")
    if probe:
        return Path(probe).resolve()

    for candidate in (current, *current.parents):
        if (candidate / "specs").is_dir() and (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError("Unable to discover repository root")


def normalize_repository_id(remote: str) -> str:
    value = remote.strip()
    ssh_match = re.match(r"git@[^:]+:(?P<path>.+?)(?:\.git)?$", value)
    if ssh_match:
        return ssh_match.group("path")
    https_match = re.match(r"https?://[^/]+/(?P<path>.+?)(?:\.git)?$", value)
    if https_match:
        return https_match.group("path")
    file_match = re.match(r"file://(?P<path>.+)$", value)
    if file_match:
        return Path(file_match.group("path")).name
    return value.removesuffix(".git")


def discover_repository_id(repo_root: Path) -> str:
    explicit = os.getenv("GRAPH_REPOSITORY_ID")
    if explicit:
        return explicit.strip()
    remote = _run_git(repo_root, "config", "--get", "remote.origin.url")
    if remote:
        return normalize_repository_id(remote)
    return repo_root.name


def load_settings(
    repo_root: Path | None = None,
    config_path: Path | None = None,
) -> GraphSettings:
    resolved_repo = discover_repo_root(repo_root)
    tool_root = Path(__file__).resolve().parents[2]
    path = config_path or tool_root / "config.yaml"
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    neo4j_raw = raw.get("neo4j", {})
    context_raw = raw.get("context", {})
    sync_raw = raw.get("sync", {})
    validation_raw = raw.get("validation", {})

    return GraphSettings(
        tool_root=tool_root,
        repo_root=resolved_repo,
        repository_id=discover_repository_id(resolved_repo),
        neo4j=Neo4jSettings(
            uri=os.getenv("NEO4J_URI", str(neo4j_raw.get("uri", "bolt://127.0.0.1:7687"))),
            user=os.getenv("NEO4J_USER", str(neo4j_raw.get("user", "neo4j"))),
            password=os.getenv("NEO4J_PASSWORD", "cpxlabs-graph-local"),
            database=os.getenv("NEO4J_DATABASE", str(neo4j_raw.get("database", "neo4j"))),
        ),
        context=ContextBudget(
            max_depth=int(context_raw.get("max_depth", 3)),
            max_nodes=int(context_raw.get("max_nodes", 80)),
        ),
        validation_rules={
            str(name): str(severity)
            for name, severity in (validation_raw.get("rules", {}) or {}).items()
        },
        historical_spec_prefixes=tuple(
            str(value) for value in validation_raw.get("historical_spec_prefixes", [])
        ),
        specs_glob=str(sync_raw.get("specs_glob", "specs/[0-9][0-9][0-9]-*/spec.md")),
        tasks_name=str(sync_raw.get("tasks_name", "tasks.md")),
        plans_name=str(sync_raw.get("plans_name", "plan.md")),
        adr_glob=str(sync_raw.get("adr_glob", "docs/adr/[0-9][0-9][0-9][0-9]-*.md")),
        prune_stale=bool(sync_raw.get("prune_stale", True)),
    )
