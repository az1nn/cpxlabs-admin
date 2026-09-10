from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .config import current_git_revision
from .context import ContextPackage, PACKAGE_VERSION


@dataclass(frozen=True, slots=True)
class FreshnessReport:
    status: str
    package_revision: str
    current_revision: str | None
    strict: bool
    valid_schema: bool
    repository_matches: bool
    messages: tuple[str, ...]

    @property
    def valid(self) -> bool:
        if not self.valid_schema or not self.repository_matches:
            return False
        if self.strict:
            return self.status == "current"
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "packageRevision": self.package_revision,
            "currentRevision": self.current_revision,
            "strict": self.strict,
            "validSchema": self.valid_schema,
            "repositoryMatches": self.repository_matches,
            "valid": self.valid,
            "messages": list(self.messages),
        }


def load_context_package(path: Path) -> ContextPackage:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"Context package not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Context package is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise ValueError("Context package root must be a JSON object")
    package = ContextPackage.from_dict(raw)
    _validate_contract(package)
    return package


def _validate_contract(package: ContextPackage) -> None:
    if package.package_version != PACKAGE_VERSION:
        raise ValueError(f"Unsupported context package version: {package.package_version}")
    if not package.repository.strip():
        raise ValueError("Context package repository is required")
    if not package.source_revision.strip():
        raise ValueError("Context package sourceRevision is required")
    if not str(package.task.get("canonicalId") or "").strip():
        raise ValueError("Context package task canonicalId is required")
    if package.budget.max_depth < 1 or package.budget.max_depth > 5:
        raise ValueError("Context package maxDepth is outside the supported range")
    if package.budget.max_nodes < 1 or package.budget.max_nodes > 500:
        raise ValueError("Context package maxNodes is outside the supported range")
    if package.budget.max_bytes < 1024 or package.budget.max_bytes > 10_000_000:
        raise ValueError("Context package maxBytes is outside the supported range")
    if package.summary.included_nodes < 1:
        raise ValueError("Context package must include at least the Task node")
    if package.summary.rendered_bytes < 1:
        raise ValueError("Context package renderedBytes must be positive")


def inspect_freshness(
    package: ContextPackage,
    repo_root: Path,
    *,
    expected_repository: str | None = None,
    strict: bool = False,
) -> FreshnessReport:
    current = current_git_revision(repo_root)
    if current is None:
        status = "unknown"
    elif package.source_revision == current:
        status = "current"
    else:
        status = "stale"

    repository_matches = expected_repository is None or package.repository == expected_repository
    messages: list[str] = []
    if not repository_matches:
        messages.append(
            f"Package repository {package.repository!r} does not match expected repository {expected_repository!r}"
        )
    if status == "stale":
        messages.append(
            f"Package revision {package.source_revision} differs from current HEAD {current}"
        )
    elif status == "unknown":
        messages.append("Current Git HEAD could not be resolved")
    else:
        messages.append("Package revision matches current Git HEAD")

    return FreshnessReport(
        status=status,
        package_revision=package.source_revision,
        current_revision=current,
        strict=strict,
        valid_schema=True,
        repository_matches=repository_matches,
        messages=tuple(messages),
    )
