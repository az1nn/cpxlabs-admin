# Quickstart: GraphRAG V4

## Prerequisites

- repository checkout at the revision you intend to query;
- Python Engineering Graph environment installed;
- Neo4j available for graph expansion;
- `graph-engineering sync` and `graph-engineering validate` completed.

GraphRAG retrieval can build/search its derived sidecar index independently, but graph expansion requires the current Neo4j projection.

## Offline deterministic flow

```bash
cd engineering-graph

graph-engineering graphrag-build \
  --provider hashing \
  --output .graphrag/index.json

graph-engineering graphrag-validate \
  .graphrag/index.json \
  --strict

graph-engineering graphrag-query \
  "execution worktree lease architecture" \
  --index .graphrag/index.json \
  --provider hashing \
  --top-k 5 \
  --depth 2 \
  --max-nodes 40 \
  --json
```

The hashing provider is intended for deterministic offline mechanics and CI. It is not equivalent to a learned semantic model.

## Learned HTTP embedding flow

Configure an embedding endpoint through environment variables/config. Credentials remain process-local and are never written to the index.

```bash
export GRAPH_RAG_EMBEDDING_URL='https://embedding-service.example/v1/embeddings'
export GRAPH_RAG_EMBEDDING_MODEL='your-embedding-model'
export GRAPH_RAG_EMBEDDING_API_KEY='...'

graph-engineering graphrag-build \
  --provider http \
  --output .graphrag/index.json

graph-engineering graphrag-query \
  "where is authorization authority defined?" \
  --index .graphrag/index.json \
  --provider http \
  --mode architecture
```

## Freshness

A strict query requires the index to match current Git HEAD and the active provider/model/config contract.

After any relevant repository revision change:

```bash
graph-engineering sync
graph-engineering validate
graph-engineering graphrag-build --provider <provider>
graph-engineering graphrag-validate .graphrag/index.json --strict
```

Do not bypass strict freshness because old retrieval results look plausible.

## Interpreting results

Results contain separate evidence layers:

1. `semanticHits` — chunks selected by vector similarity;
2. `anchors` — existing deterministic Engineering Graph nodes resolved from hit paths;
3. `graphEvidence` — bounded traversal over relationships already present in Neo4j.

A high semantic score is not proof that two graph entities are related. Only deterministic projected relationships are graph evidence.

## Architecture discovery

Use architecture mode when the query is specifically about design decisions/requirements:

```bash
graph-engineering graphrag-query \
  "why does the engineering graph stay outside product runtime?" \
  --mode architecture \
  --top-k 8
```

This prioritizes/retains ADR, Spec and Requirement evidence while preserving provenance.

## Disposal

GraphRAG state is disposable:

```bash
rm -rf engineering-graph/.graphrag
```

Deleting it never deletes canonical repository knowledge or deterministic Neo4j authority.
