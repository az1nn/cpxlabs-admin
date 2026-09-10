from __future__ import annotations

from collections import defaultdict
from contextlib import AbstractContextManager
import time
from typing import Any, Iterable

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from .config import GraphSettings
from .model import CORE_LABELS, CORE_RELATIONSHIPS, GraphEdge, GraphNode
from .schema import constraint_statements, validate_schema_definitions


class GraphStore(AbstractContextManager["GraphStore"]):
    def __init__(self, settings: GraphSettings) -> None:
        self.settings = settings
        self.driver = GraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.user, settings.neo4j.password),
        )

    def __enter__(self) -> "GraphStore":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        self.driver.close()

    def verify_connectivity(self) -> None:
        self.driver.verify_connectivity()

    def wait_until_ready(self, timeout_seconds: int) -> None:
        deadline = time.monotonic() + max(timeout_seconds, 0)
        last_error: Exception | None = None
        while True:
            try:
                self.verify_connectivity()
                return
            except Exception as error:  # driver raises multiple connectivity subclasses
                last_error = error
                if time.monotonic() >= deadline:
                    raise RuntimeError(
                        f"Neo4j was not ready within {timeout_seconds}s: {last_error}"
                    ) from error
                time.sleep(1)

    def run(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.driver.session(database=self.settings.neo4j.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    def initialize_schema(self) -> None:
        validate_schema_definitions(self.settings)
        for statement in constraint_statements(self.settings):
            self.run(statement)

    def upsert_nodes(
        self,
        nodes: Iterable[GraphNode],
        repository: str,
        source_revision: str,
        sync_run_id: str,
    ) -> None:
        grouped: dict[str, list[GraphNode]] = defaultdict(list)
        for node in nodes:
            if node.label not in CORE_LABELS:
                raise ValueError(f"Unsupported node label: {node.label}")
            grouped[node.label].append(node)

        for label, values in grouped.items():
            rows = []
            for node in values:
                properties = {
                    **node.properties,
                    "repository": repository,
                    "canonicalId": node.canonical_id,
                    "sourceRevision": source_revision,
                    "syncRunId": sync_run_id,
                }
                rows.append(
                    {
                        "repository": repository,
                        "canonicalId": node.canonical_id,
                        "properties": properties,
                    }
                )
            query = f"""
            UNWIND $rows AS row
            MERGE (n:{label} {{repository: row.repository, canonicalId: row.canonicalId}})
            SET n += row.properties
            """
            self.run(query, {"rows": rows})

    def upsert_edges(
        self,
        edges: Iterable[GraphEdge],
        repository: str,
        source_revision: str,
        sync_run_id: str,
    ) -> None:
        grouped: dict[tuple[str, str, str], list[GraphEdge]] = defaultdict(list)
        for edge in edges:
            if edge.relationship not in CORE_RELATIONSHIPS:
                raise ValueError(f"Unsupported relationship: {edge.relationship}")
            if edge.source_label not in CORE_LABELS or edge.target_label not in CORE_LABELS:
                raise ValueError("Unsupported edge endpoint label")
            grouped[(edge.source_label, edge.relationship, edge.target_label)].append(edge)

        for (source_label, relationship, target_label), values in grouped.items():
            rows = []
            for edge in values:
                properties = {
                    **edge.properties,
                    "repository": repository,
                    "sourceRevision": source_revision,
                    "syncRunId": sync_run_id,
                }
                rows.append(
                    {
                        "repository": repository,
                        "sourceId": edge.source_id,
                        "targetId": edge.target_id,
                        "properties": properties,
                    }
                )
            query = f"""
            UNWIND $rows AS row
            MATCH (source:{source_label} {{repository: row.repository, canonicalId: row.sourceId}})
            MATCH (target:{target_label} {{repository: row.repository, canonicalId: row.targetId}})
            MERGE (source)-[r:{relationship}]->(target)
            SET r += row.properties
            """
            self.run(query, {"rows": rows})

    def prune_stale(self, repository: str, sync_run_id: str) -> None:
        self.run(
            """
            MATCH ()-[r]->()
            WHERE r.repository = $repository
              AND coalesce(r.syncRunId, '') <> $syncRunId
            DELETE r
            """,
            {"repository": repository, "syncRunId": sync_run_id},
        )
        self.run(
            """
            MATCH (n)
            WHERE n.repository = $repository
              AND coalesce(n.syncRunId, '') <> $syncRunId
            DETACH DELETE n
            """,
            {"repository": repository, "syncRunId": sync_run_id},
        )

    def reset_repository(self, repository: str) -> None:
        self.run(
            "MATCH (n {repository: $repository}) DETACH DELETE n",
            {"repository": repository},
        )

    def query_file(self, filename: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        query_path = self.settings.tool_root / "queries" / filename
        return self.run(query_path.read_text(encoding="utf-8"), parameters)
