from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import Any, Iterable

import yaml


_FRONTMATTER_BOUNDARY = "---"
_SPEC_DIR_RE = re.compile(r"^(?P<number>\d{3})-(?P<slug>[a-z0-9][a-z0-9-]*)$")
_REQUIREMENT_RE = re.compile(
    r"^\s*-\s+(?:\*\*)?(?P<id>(?:FR|SC)-\d{3})(?:\*\*)?\s*:\s*(?P<text>.+?)\s*$"
)
_TASK_RE = re.compile(r"^\s*-\s+\[(?P<done>[ xX])\]\s+(?P<id>T\d{3})\s*(?P<text>.*)$")
_ADR_FILE_RE = re.compile(r"^(?P<number>\d{4})-(?P<slug>.+)\.md$")
_ADR_REF_RE = re.compile(r"\bADR-(?P<number>\d{4})\b", re.IGNORECASE)
_SPEC_REF_RE = re.compile(r"\bSPEC-(?P<number>\d{3})-[A-Z0-9-]+\b", re.IGNORECASE)
# Accept canonical task dependency markers in either human-friendly form:
#   (depends: T001,T002)
#   (`depends: T001,T002`)
#   `depends: T001,T002`
# Only explicit T### identifiers become dependency edges; prose/phase order never does.
_TASK_DEPENDS_RE = re.compile(
    r"(?:\(\s*)?`?\s*depends\s*:\s*(?P<ids>T\d{3}(?:\s*,\s*T\d{3})*)\s*`?(?:\s*\))?",
    re.IGNORECASE,
)
_TASK_ID_RE = re.compile(r"\bT\d{3}\b", re.IGNORECASE)
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_PLAIN_PATH_RE = re.compile(
    r"(?<![\w:/.-])(?P<path>(?:apps|packages|docs|specs|tests|scripts|engineering-graph|\.github|\.specify)/[A-Za-z0-9_./$-]+\.[A-Za-z0-9]+)"
)
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_STATUS_RE = re.compile(r"^\*\*Status\*\*:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)
_USER_STORY_RE = re.compile(r"\[(US\d+)\]", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class ParsedFrontmatter:
    metadata: dict[str, Any]
    body: str
    body_start_line: int


@dataclass(frozen=True, slots=True)
class ParsedRequirement:
    source_id: str
    kind: str
    text: str
    line: int
    critical: bool


@dataclass(frozen=True, slots=True)
class ParsedTask:
    source_id: str
    title: str
    status: str
    line: int
    phase: str | None
    parallel: bool
    user_story: str | None
    dependencies: tuple[str, ...]
    paths: tuple[str, ...]


def parse_frontmatter(text: str) -> ParsedFrontmatter:
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_BOUNDARY:
        return ParsedFrontmatter({}, text, 1)

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == _FRONTMATTER_BOUNDARY:
            end_index = index
            break
    if end_index is None:
        raise ValueError("Unterminated YAML frontmatter")

    raw = "\n".join(lines[1:end_index])
    metadata = yaml.safe_load(raw) or {}
    if not isinstance(metadata, dict):
        raise ValueError("Markdown frontmatter must be a mapping")
    body = "\n".join(lines[end_index + 1 :])
    return ParsedFrontmatter(metadata, body, end_index + 2)


def canonical_spec_id(feature_dir_name: str) -> str:
    match = _SPEC_DIR_RE.match(feature_dir_name)
    if not match:
        raise ValueError(f"Invalid Spec Kit feature directory: {feature_dir_name}")
    return f"SPEC-{match.group('number')}-{match.group('slug').upper()}"


def canonical_requirement_id(spec_id: str, source_id: str) -> str:
    return f"{spec_id}:{source_id.upper()}"


def canonical_task_id(spec_id: str, source_id: str) -> str:
    value = source_id.upper()
    if not re.fullmatch(r"T\d{3}", value):
        raise ValueError(f"Invalid task id: {source_id}")
    return f"{spec_id}:{value}"


def canonical_adr_id(filename: str) -> str:
    match = _ADR_FILE_RE.match(filename)
    if not match:
        raise ValueError(f"Invalid ADR filename: {filename}")
    return f"ADR-{match.group('number')}"


def normalize_path(value: str) -> str:
    path = value.strip().strip(".,;:()[]{}")
    if path.startswith("./"):
        path = path[2:]
    normalized = PurePosixPath(path).as_posix()
    while normalized.startswith("../"):
        normalized = normalized[3:]
    return normalized


def is_test_path(path: str) -> bool:
    lower = path.lower()
    name = PurePosixPath(lower).name
    parts = set(PurePosixPath(lower).parts)
    return (
        "tests" in parts
        or "test" in parts
        or "e2e" in parts
        or "storybook" in parts
        or ".test." in name
        or ".spec." in name
        or ".stories." in name
    )


def test_kind(path: str) -> str:
    lower = path.lower()
    if "e2e" in lower or "playwright" in lower:
        return "e2e"
    if "storybook" in lower or ".stories." in lower:
        return "storybook"
    if "integration" in lower:
        return "integration"
    if "architecture" in lower:
        return "architecture"
    if ".test." in lower or "/tests/" in f"/{lower}/":
        return "unit"
    return "other"


def code_kind(path: str) -> str:
    lower = path.lower()
    if lower.startswith("docs/") or lower.startswith("specs/"):
        return "docs"
    if lower.startswith(".github/") or lower.endswith((".yml", ".yaml", ".json", ".toml")):
        return "config"
    if lower.startswith("scripts/") or lower.endswith((".sh", ".py")):
        return "script"
    if lower.startswith(("apps/", "packages/")):
        return "source"
    return "other"


def extract_paths(text: str) -> tuple[str, ...]:
    candidates: set[str] = set()
    for inline in _INLINE_CODE_RE.findall(text):
        token = inline.strip()
        if " " in token or token.startswith(("http://", "https://")):
            continue
        if "/" in token and "." in PurePosixPath(token).name:
            candidates.add(normalize_path(token))
    for match in _PLAIN_PATH_RE.finditer(text):
        candidates.add(normalize_path(match.group("path")))
    return tuple(sorted(candidates))


def extract_adr_refs(text: str) -> tuple[str, ...]:
    return tuple(sorted({f"ADR-{match.group('number')}" for match in _ADR_REF_RE.finditer(text)}))


def extract_spec_refs(text: str) -> tuple[str, ...]:
    return tuple(sorted({match.group(0).upper() for match in _SPEC_REF_RE.finditer(text)}))


def extract_title(text: str, fallback: str) -> str:
    match = _H1_RE.search(text)
    return match.group(1).strip() if match else fallback


def extract_status(text: str, metadata: dict[str, Any], fallback: str = "active") -> str:
    graph = metadata.get("graph", {}) if isinstance(metadata, dict) else {}
    if isinstance(graph, dict) and graph.get("status"):
        return str(graph["status"]).strip().lower()
    match = _STATUS_RE.search(text)
    return match.group(1).strip().lower() if match else fallback


def graph_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    value = metadata.get("graph", {}) if isinstance(metadata, dict) else {}
    return value if isinstance(value, dict) else {}


def parse_requirements(text: str, body_start_line: int = 1) -> list[ParsedRequirement]:
    result: list[ParsedRequirement] = []
    for offset, line in enumerate(text.splitlines(), start=body_start_line):
        match = _REQUIREMENT_RE.match(line)
        if not match:
            continue
        source_id = match.group("id").upper()
        statement = match.group("text").strip()
        result.append(
            ParsedRequirement(
                source_id=source_id,
                kind="functional" if source_id.startswith("FR-") else "success_criterion",
                text=statement,
                line=offset,
                critical="MUST" in statement.upper(),
            )
        )
    return result


def _parse_task_dependencies(text: str) -> tuple[str, ...]:
    match = _TASK_DEPENDS_RE.search(text)
    if not match:
        return ()
    return tuple(sorted({value.upper() for value in _TASK_ID_RE.findall(match.group("ids"))}))


def parse_tasks(text: str, body_start_line: int = 1) -> list[ParsedTask]:
    result: list[ParsedTask] = []
    phase: str | None = None
    for offset, line in enumerate(text.splitlines(), start=body_start_line):
        if line.startswith("## "):
            phase = line[3:].strip()
            continue
        match = _TASK_RE.match(line)
        if not match:
            continue
        raw_text = match.group("text").strip()
        user_story_match = _USER_STORY_RE.search(raw_text)
        title = _TASK_DEPENDS_RE.sub("", raw_text).strip()
        result.append(
            ParsedTask(
                source_id=match.group("id").upper(),
                title=title,
                status="done" if match.group("done").lower() == "x" else "pending",
                line=offset,
                phase=phase,
                parallel="[P]" in raw_text.upper(),
                user_story=user_story_match.group(1).upper() if user_story_match else None,
                dependencies=_parse_task_dependencies(raw_text),
                paths=extract_paths(raw_text),
            )
        )
    return result


def frontmatter_list(graph: dict[str, Any], key: str) -> tuple[str, ...]:
    value = graph.get(key, [])
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable) and not isinstance(value, (dict, bytes)):
        return tuple(str(item) for item in value)
    raise ValueError(f"graph.{key} must be a string or list")
