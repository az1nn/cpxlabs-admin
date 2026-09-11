from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .config import GraphSettings
from .model import CORE_LABELS, CORE_RELATIONSHIPS


class SchemaDefinitionError(RuntimeError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise SchemaDefinitionError(f"Schema file must contain a mapping: {path}")
    return value


def load_node_schema(settings: GraphSettings) -> dict[str, Any]:
    return _load_yaml(settings.tool_root / "schema" / "nodes.yaml")


def load_relationship_schema(settings: GraphSettings) -> dict[str, Any]:
    return _load_yaml(settings.tool_root / "schema" / "relationships.yaml")


def validate_schema_definitions(settings: GraphSettings) -> None:
    nodes = load_node_schema(settings)
    relationships = load_relationship_schema(settings)
    node_names = set((nodes.get("nodes") or {}).keys())
    relationship_names = set((relationships.get("relationships") or {}).keys())

    if node_names != set(CORE_LABELS):
        missing = sorted(CORE_LABELS - node_names)
        extra = sorted(node_names - CORE_LABELS)
        raise SchemaDefinitionError(f"Node schema mismatch; missing={missing}, extra={extra}")
    if relationship_names != set(CORE_RELATIONSHIPS):
        missing = sorted(CORE_RELATIONSHIPS - relationship_names)
        extra = sorted(relationship_names - CORE_RELATIONSHIPS)
        raise SchemaDefinitionError(
            f"Relationship schema mismatch; missing={missing}, extra={extra}"
        )

    for label, definition in (nodes.get("nodes") or {}).items():
        if not isinstance(definition, dict):
            raise SchemaDefinitionError(f"Node {label} definition must be a mapping")
        identity = definition.get("identity")
        if identity != ["repository", "canonicalId"]:
            raise SchemaDefinitionError(
                f"Node {label} identity must be [repository, canonicalId]"
            )

    allowed_endpoints = set(CORE_LABELS)
    for name, definition in (relationships.get("relationships") or {}).items():
        if not isinstance(definition, dict):
            raise SchemaDefinitionError(f"Relationship {name} definition must be a mapping")
        sources = set(definition.get("from") or [])
        targets = set(definition.get("to") or [])
        if not sources or not targets:
            raise SchemaDefinitionError(f"Relationship {name} requires from/to labels")
        unknown = (sources | targets) - allowed_endpoints
        if unknown:
            raise SchemaDefinitionError(
                f"Relationship {name} references unknown labels: {sorted(unknown)}"
            )


def constraint_statements(settings: GraphSettings) -> list[str]:
    raw = (settings.tool_root / "schema" / "constraints.cypher").read_text(encoding="utf-8")
    return [statement.strip() for statement in raw.split(";") if statement.strip()]
