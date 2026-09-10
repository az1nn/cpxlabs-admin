from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .context import ContextPackage

SUPPORTED_AGENTS = ("codex", "claude")


def _canonical_paths(package: ContextPackage) -> tuple[str, ...]:
    values: set[str] = set()

    def add_entity(entity: dict[str, object] | None) -> None:
        if not entity:
            return
        value = entity.get("sourcePath") or entity.get("path")
        if value:
            values.add(str(value))

    add_entity(package.task)
    add_entity(package.spec)
    for group in (
        package.requirements,
        package.adrs,
        package.dependencies,
        package.code_artifacts,
        package.tests,
    ):
        for entity in group:
            add_entity(entity)
    return tuple(sorted(values))


def validation_commands(package: ContextPackage) -> tuple[str, ...]:
    paths = _canonical_paths(package)
    commands: list[str] = []
    if any(path.startswith("engineering-graph/") for path in paths):
        commands.extend(
            [
                "python -m unittest discover -s engineering-graph/tests -v",
                "graph-engineering validate",
            ]
        )
    if any(path.startswith(("apps/", "packages/")) for path in paths):
        commands.extend(["pnpm typecheck", "pnpm test", "pnpm build"])
    if not commands:
        commands.append("git diff --check")
    # Preserve order while removing duplicates.
    return tuple(dict.fromkeys(commands))


def _path_lines(paths: Iterable[str]) -> list[str]:
    values = list(paths)
    return [f"- `{path}`" for path in values] if values else ["- No canonical paths linked"]


def _shared_sections(package: ContextPackage, context_json_path: str) -> list[str]:
    task_id = str(package.task.get("canonicalId") or "unknown")
    paths = _canonical_paths(package)
    commands = validation_commands(package)
    return [
        f"Task: `{task_id}`",
        f"Repository: `{package.repository}`",
        f"Source revision: `{package.source_revision}`",
        f"Portable context: `{context_json_path}`",
        "",
        "## Canonical files to inspect",
        *_path_lines(paths),
        "",
        "## Validation commands",
        *[f"- `{command}`" for command in commands],
        "",
        "## Authority rule",
        "The generated context package and Neo4j are derived navigation aids. Read the canonical repository files above before editing; Git/Markdown/code/tests remain authoritative.",
    ]


def render_codex_handoff(package: ContextPackage, context_json_path: str = "context.json") -> str:
    lines = [
        f"# Codex Handoff — {package.task.get('canonicalId', 'Task')}",
        "",
        "Follow the repository `AGENTS.md` instructions that apply to every file you touch. Use this handoff as a task map, not as a replacement for repository documentation.",
        "",
        *_shared_sections(package, context_json_path),
        "",
        "## Execution boundary",
        "Implement only the requested task scope. Do not infer missing authoritative graph edges. Do not merge or bypass repository validation gates unless explicitly instructed by the user.",
        "",
    ]
    return "\n".join(lines)


def render_claude_handoff(package: ContextPackage, context_json_path: str = "context.json") -> str:
    lines = [
        f"# Claude Code Handoff — {package.task.get('canonicalId', 'Task')}",
        "",
        "Use the repository's persistent instructions and the portable context package as orientation. Keep progress in Git/repository artifacts rather than creating a separate source of truth for this task.",
        "",
        *_shared_sections(package, context_json_path),
        "",
        "## Execution boundary",
        "Work incrementally from the canonical files and run the validation commands above. Do not treat this generated handoff as canonical documentation and do not perform merge/push actions unless explicitly authorized.",
        "",
    ]
    return "\n".join(lines)


def render_agent_handoff(
    package: ContextPackage,
    agent: str,
    context_json_path: str = "context.json",
) -> str:
    if agent == "codex":
        return render_codex_handoff(package, context_json_path)
    if agent == "claude":
        return render_claude_handoff(package, context_json_path)
    raise ValueError(f"Unsupported agent adapter: {agent}. Expected one of {', '.join(SUPPORTED_AGENTS)}")


def write_agent_handoff(
    package: ContextPackage,
    agent: str,
    output: Path,
    context_json_path: str = "context.json",
) -> str:
    rendered = render_agent_handoff(package, agent, context_json_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    return rendered
