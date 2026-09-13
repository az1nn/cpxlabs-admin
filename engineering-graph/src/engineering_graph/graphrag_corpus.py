from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import subprocess
from typing import Iterable

from .config import GraphSettings


@dataclass(frozen=True, slots=True)
class CorpusChunk:
    chunk_id: str
    source_path: str
    ordinal: int
    start_line: int
    end_line: int
    text: str
    content_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "chunkId": self.chunk_id,
            "sourcePath": self.source_path,
            "ordinal": self.ordinal,
            "startLine": self.start_line,
            "endLine": self.end_line,
            "text": self.text,
            "contentSha256": self.content_sha256,
        }


def git_tracked_paths(repo_root: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    values = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        values.append(raw.decode("utf-8"))
    return tuple(sorted(values))


def _is_excluded(path: str, excluded_prefixes: Iterable[str]) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    for prefix in excluded_prefixes:
        candidate = prefix.replace("\\", "/").strip("/")
        if not candidate:
            continue
        if normalized == candidate or normalized.startswith(f"{candidate}/"):
            return True
    return False


def eligible_tracked_paths(settings: GraphSettings) -> tuple[str, ...]:
    extensions = {value.lower() for value in settings.graphrag.include_extensions}
    selected: list[str] = []
    for path in git_tracked_paths(settings.repo_root):
        if _is_excluded(path, settings.graphrag.excluded_prefixes):
            continue
        if Path(path).suffix.lower() not in extensions:
            continue
        selected.append(path.replace("\\", "/"))
    return tuple(sorted(selected))


def normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized.split("\n"))


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, max(offset, 0)) + 1


def chunk_text(
    repository: str,
    source_path: str,
    text: str,
    *,
    max_chars: int,
    overlap_chars: int,
) -> tuple[CorpusChunk, ...]:
    if max_chars <= 0:
        raise ValueError("GraphRAG chunk max_chars must be positive")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("GraphRAG chunk overlap must be >= 0 and smaller than max_chars")

    normalized = normalize_text(text)
    if not normalized.strip():
        return ()

    chunks: list[CorpusChunk] = []
    start = 0
    ordinal = 0
    length = len(normalized)

    while start < length:
        end = min(start + max_chars, length)
        if end < length:
            minimum_break = start + max_chars // 2
            newline = normalized.rfind("\n", minimum_break, end)
            if newline > start:
                end = newline + 1

        raw = normalized[start:end]
        chunk_value = raw.strip()
        if chunk_value:
            content_sha = hashlib.sha256(chunk_value.encode("utf-8")).hexdigest()
            identity = (
                f"{repository}\0{source_path}\0{ordinal}\0{content_sha}"
            ).encode("utf-8")
            chunk_id = hashlib.sha256(identity).hexdigest()[:32]
            chunks.append(
                CorpusChunk(
                    chunk_id=chunk_id,
                    source_path=source_path,
                    ordinal=ordinal,
                    start_line=_line_number(normalized, start),
                    end_line=_line_number(normalized, max(end - 1, start)),
                    text=chunk_value,
                    content_sha256=content_sha,
                )
            )
            ordinal += 1

        if end >= length:
            break
        start = max(end - overlap_chars, start + 1)

    return tuple(chunks)


def build_corpus(settings: GraphSettings) -> tuple[CorpusChunk, ...]:
    chunks: list[CorpusChunk] = []
    for relative in eligible_tracked_paths(settings):
        path = settings.repo_root / relative
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        chunks.extend(
            chunk_text(
                settings.repository_id,
                relative,
                text,
                max_chars=settings.graphrag.chunk_max_chars,
                overlap_chars=settings.graphrag.chunk_overlap_chars,
            )
        )
    return tuple(sorted(chunks, key=lambda item: (item.source_path, item.ordinal, item.chunk_id)))
