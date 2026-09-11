from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

CORE_LABELS = frozenset(
    {
        "Requirement",
        "Spec",
        "ADR",
        "Task",
        "CodeArtifact",
        "Test",
        "PullRequest",
    }
)

CORE_RELATIONSHIPS = frozenset(
    {
        "REALIZED_BY",
        "CONSTRAINED_BY",
        "DECOMPOSED_INTO",
        "DEPENDS_ON",
        "IMPLEMENTED_BY",
        "VALIDATED_BY",
        "IMPLEMENTS",
        "CHANGES",
    }
)

_UNIQUE_SOURCE_LABELS = frozenset({"Requirement", "Spec", "ADR", "Task", "PullRequest"})
_OPERATIONAL_PROPERTIES = frozenset({"sourceRevision", "syncRunId"})


@dataclass(frozen=True, slots=True)
class GraphNode:
    label: str
    canonical_id: str
    properties: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str]:
        return (self.label, self.canonical_id)


@dataclass(frozen=True, slots=True)
class GraphEdge:
    source_label: str
    source_id: str
    relationship: str
    target_label: str
    target_id: str
    properties: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str, str, str, str]:
        return (
            self.source_label,
            self.source_id,
            self.relationship,
            self.target_label,
            self.target_id,
        )


@dataclass(frozen=True, slots=True)
class ExtractionIssue:
    code: str
    message: str
    source_path: str | None = None
    entity_id: str | None = None


class GraphModel:
    def __init__(self) -> None:
        self.nodes: dict[tuple[str, str], GraphNode] = {}
        self.edges: dict[tuple[str, str, str, str, str], GraphEdge] = {}
        self.issues: list[ExtractionIssue] = []

    def add_node(self, node: GraphNode) -> None:
        if node.label not in CORE_LABELS:
            raise ValueError(f"Unsupported node label: {node.label}")
        if not node.canonical_id.strip():
            raise ValueError("Node canonical_id cannot be blank")

        existing = self.nodes.get(node.key())
        if existing is None:
            self.nodes[node.key()] = node
            return

        if node.label in _UNIQUE_SOURCE_LABELS:
            existing_source = existing.properties.get("sourcePath")
            new_source = node.properties.get("sourcePath")
            if existing_source and new_source and existing_source != new_source:
                raise ValueError(
                    f"Duplicate canonical id {node.label}:{node.canonical_id} "
                    f"from {existing_source} and {new_source}"
                )

        merged = dict(existing.properties)
        for key, value in node.properties.items():
            if value is not None:
                merged[key] = value
        self.nodes[node.key()] = GraphNode(node.label, node.canonical_id, merged)

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.relationship not in CORE_RELATIONSHIPS:
            raise ValueError(f"Unsupported relationship: {edge.relationship}")
        if edge.source_label not in CORE_LABELS or edge.target_label not in CORE_LABELS:
            raise ValueError(
                f"Unsupported relationship endpoints: {edge.source_label}->{edge.target_label}"
            )
        existing = self.edges.get(edge.key())
        if existing is None:
            self.edges[edge.key()] = edge
            return
        merged = dict(existing.properties)
        for key, value in edge.properties.items():
            if value is not None:
                merged[key] = value
        self.edges[edge.key()] = GraphEdge(
            edge.source_label,
            edge.source_id,
            edge.relationship,
            edge.target_label,
            edge.target_id,
            merged,
        )

    def add_issue(self, issue: ExtractionIssue) -> None:
        self.issues.append(issue)

    def node(self, label: str, canonical_id: str) -> GraphNode | None:
        return self.nodes.get((label, canonical_id))

    def nodes_by_label(self, label: str) -> list[GraphNode]:
        return sorted(
            (node for node in self.nodes.values() if node.label == label),
            key=lambda node: node.canonical_id,
        )

    def edges_from(
        self,
        label: str,
        canonical_id: str,
        relationship: str | None = None,
    ) -> list[GraphEdge]:
        return sorted(
            (
                edge
                for edge in self.edges.values()
                if edge.source_label == label
                and edge.source_id == canonical_id
                and (relationship is None or edge.relationship == relationship)
            ),
            key=lambda edge: edge.key(),
        )

    def dangling_edges(self) -> list[GraphEdge]:
        return [
            edge
            for edge in self.edges.values()
            if (edge.source_label, edge.source_id) not in self.nodes
            or (edge.target_label, edge.target_id) not in self.nodes
        ]

    def logical_signature(self) -> tuple[tuple[Any, ...], tuple[Any, ...]]:
        def stable_properties(properties: dict[str, Any]) -> tuple[tuple[str, str], ...]:
            return tuple(
                sorted(
                    (key, repr(value))
                    for key, value in properties.items()
                    if key not in _OPERATIONAL_PROPERTIES
                )
            )

        nodes = tuple(
            sorted(
                (
                    node.label,
                    node.canonical_id,
                    stable_properties(node.properties),
                )
                for node in self.nodes.values()
            )
        )
        edges = tuple(
            sorted(
                (
                    *edge.key(),
                    stable_properties(edge.properties),
                )
                for edge in self.edges.values()
            )
        )
        return nodes, edges

    def extend_nodes(self, nodes: Iterable[GraphNode]) -> None:
        for node in nodes:
            self.add_node(node)

    def extend_edges(self, edges: Iterable[GraphEdge]) -> None:
        for edge in edges:
            self.add_edge(edge)
