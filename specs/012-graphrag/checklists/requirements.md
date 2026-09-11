# Requirements Checklist: GraphRAG V4

## Authority and scope

- [x] Canonical Git/Markdown/code/tests remain authoritative.
- [x] Embeddings/index/results are explicitly derived/disposable.
- [x] Semantic similarity cannot create canonical graph edges.
- [x] Product runtime remains independent from Engineering Graph/GraphRAG.
- [x] V4 excludes autonomous commit/push/PR/merge and agent supervision.

## Retrieval contract

- [x] Corpus is limited to Git-tracked eligible files.
- [x] Chunk identity/provenance requirements are explicit.
- [x] Provider/model/dimension identity is explicit.
- [x] Learned provider and deterministic offline provider roles are distinguished.
- [x] Ranking, top-k and minimum-score behavior are explicit.

## Graph composition

- [x] Semantic hits resolve to existing graph anchors.
- [x] Expansion uses existing deterministic relationships only.
- [x] Depth/node budgets and truncation are explicit.
- [x] Semantic scores and graph evidence remain distinct.
- [x] ADR/spec discovery is retrieval assistance, not relationship inference.

## Freshness/security

- [x] Index is revision-bound.
- [x] Provider/model/config drift requires rebuild in strict mode.
- [x] Generated state is gitignored/disposable.
- [x] Untracked files cannot be indexed accidentally.
- [x] Credentials are never persisted in index metadata.

## Validation

- [x] Offline deterministic CI path is defined.
- [x] Semantic reproducibility is required.
- [x] Stale-index rejection is required.
- [x] Ephemeral Neo4j expansion validation is required.
- [x] Existing Engineering Graph and product CI remain mandatory.
