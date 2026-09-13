from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_settings
from .embeddings import build_embedding_provider
from .graphrag import query_graphrag
from .graphrag_index import (
    build_semantic_index,
    default_index_path,
    inspect_index_freshness,
    load_semantic_index,
    write_semantic_index,
)
from .store import GraphStore


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def _settings(args: argparse.Namespace):
    repo_root = Path(args.repo_root).resolve() if getattr(args, "repo_root", None) else None
    return load_settings(repo_root=repo_root)


def _provider(args: argparse.Namespace, settings):
    return build_embedding_provider(
        settings,
        provider_name=getattr(args, "provider", None),
        model_id=getattr(args, "model", None),
        dimensions=getattr(args, "dimensions", None),
    )


def _index_path(args: argparse.Namespace, settings) -> Path:
    value = getattr(args, "index", None) or getattr(args, "output", None)
    return Path(value).resolve() if value else default_index_path(settings)


def add_provider_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provider", choices=("hashing", "http"))
    parser.add_argument("--model")
    parser.add_argument("--dimensions", type=int)


def command_graphrag_build(args: argparse.Namespace) -> int:
    settings = _settings(args)
    provider = _provider(args, settings)
    destination = _index_path(args, settings)
    index = build_semantic_index(settings, provider)
    write_semantic_index(index, destination)
    payload = {
        "index": str(destination),
        "manifest": index.manifest.to_dict(),
    }
    if args.json:
        print(_json(payload))
    else:
        print(
            f"GraphRAG index built: chunks={index.manifest.chunk_count} "
            f"provider={index.manifest.provider_id}/{index.manifest.model_id} "
            f"revision={index.manifest.source_revision} path={destination}"
        )
        if index.manifest.provider_id == "hashing":
            print("NOTE: hashing provider is a deterministic offline retrieval surrogate, not a learned embedding model.")
    return 0


def command_graphrag_validate(args: argparse.Namespace) -> int:
    settings = _settings(args)
    provider = _provider(args, settings)
    path = _index_path(args, settings)
    index = load_semantic_index(path)
    report = inspect_index_freshness(index, settings, provider, strict=args.strict)
    if args.json:
        print(_json(report.to_dict()))
    else:
        print(
            f"GraphRAG index {report.status}: index={report.index_revision} "
            f"current={report.current_revision or 'unknown'}"
        )
        for message in report.messages:
            print(f"- {message}")
    return 0 if report.valid else 1


def command_graphrag_status(args: argparse.Namespace) -> int:
    settings = _settings(args)
    provider = _provider(args, settings)
    path = _index_path(args, settings)
    if not path.exists():
        payload = {
            "exists": False,
            "index": str(path),
            "providerId": provider.provider_id,
            "modelId": provider.model_id,
        }
        if args.json:
            print(_json(payload))
        else:
            print(f"GraphRAG index missing: {path}")
        return 1
    index = load_semantic_index(path)
    report = inspect_index_freshness(index, settings, provider, strict=False)
    payload = {
        "exists": True,
        "index": str(path),
        "manifest": index.manifest.to_dict(),
        "freshness": report.to_dict(),
    }
    if args.json:
        print(_json(payload))
    else:
        print(
            f"GraphRAG index: chunks={index.manifest.chunk_count} "
            f"status={report.status} provider={index.manifest.provider_id}/{index.manifest.model_id} "
            f"path={path}"
        )
    return 0 if report.valid else 1


def command_graphrag_query(args: argparse.Namespace) -> int:
    settings = _settings(args)
    provider = _provider(args, settings)
    path = _index_path(args, settings)
    index = load_semantic_index(path)
    store = GraphStore(settings)
    try:
        result = query_graphrag(
            store,
            settings,
            index,
            provider,
            args.query,
            top_k=args.top_k,
            min_score=args.min_score,
            max_depth=args.depth,
            max_nodes=args.max_nodes,
            mode=args.mode,
            strict=not args.allow_stale,
        )
    finally:
        store.close()

    payload = result.to_dict()
    if args.json:
        print(_json(payload))
        return 0

    print(
        f"GraphRAG: query={result.query!r} provider={result.provider_id}/{result.model_id} "
        f"revision={result.source_revision}"
    )
    print("Semantic hits:")
    for hit in result.semantic_hits:
        print(
            f"- {hit.score:.4f} {hit.source_path}:{hit.start_line}-{hit.end_line} "
            f"[{hit.chunk_id}]"
        )
    print("Graph anchors:")
    for anchor in result.anchors:
        print(
            f"- {anchor.label} {anchor.canonical_id} "
            f"seed={anchor.seed_source_path} score={anchor.semantic_score:.4f}"
        )
    print("Graph evidence:")
    for item in result.graph_evidence:
        print(
            f"- d={item.distance} {item.label} {item.canonical_id} "
            f"anchors={','.join(item.anchor_canonical_ids)}"
        )
    if result.truncated:
        print("TRUNCATED: graph expansion reached the configured node budget")
    return 0
