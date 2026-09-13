# Data Model: GraphRAG V4

## SemanticChunk

```text
SemanticChunk
  chunkId: string
  sourcePath: string
  ordinal: int
  startLine: int
  endLine: int
  text: string
  contentSha256: string
  vector: float[]
```

Invariants:

- `chunkId` is stable for repository/path/ordinal/content;
- `sourcePath` is repository-relative POSIX form;
- text comes only from eligible Git-tracked files;
- vectors are L2-normalized before persistence when provider output is non-zero;
- vector dimension equals index manifest dimensions.

## SemanticIndexManifest

```text
SemanticIndexManifest
  schemaVersion: string
  repository: string
  sourceRevision: string
  providerId: string
  modelId: string
  dimensions: int
  chunkMaxChars: int
  chunkOverlapChars: int
  includeExtensions: string[]
  excludedPrefixes: string[]
  chunkCount: int
  semanticSha256: string
  generatedAt: timestamp
```

`semanticSha256` excludes `generatedAt` and covers normalized manifest semantics plus chunk metadata/text/vectors.

## SemanticIndex

```text
SemanticIndex
  manifest: SemanticIndexManifest
  chunks: SemanticChunk[]
```

Ordering is deterministic by `(sourcePath, ordinal, chunkId)`.

## SemanticHit

```text
SemanticHit
  chunkId: string
  sourcePath: string
  ordinal: int
  startLine: int
  endLine: int
  score: float
  text: string
```

Ranking: `score DESC`, then deterministic path/ordinal/chunk ID tie breaks.

## GraphAnchor

```text
GraphAnchor
  seedChunkId: string
  seedSourcePath: string
  semanticScore: float
  label: string
  canonicalId: string
  sourcePath?: string
  path?: string
  title?: string
  status?: string
```

A semantic hit may map to zero, one or many anchors. Ambiguity is retained.

## GraphEvidence

```text
GraphEvidence
  seedChunkId: string
  anchorCanonicalId: string
  canonicalId: string
  label: string
  distance: int
  sourcePath?: string
  path?: string
  title?: string
  status?: string
  via: TraversalStep[]
```

`TraversalStep` records existing relationship type and direction. No semantic/inferred relationship is represented as a graph edge.

## GraphRagResult

```text
GraphRagResult
  schemaVersion: string
  repository: string
  sourceRevision: string
  indexSemanticSha256: string
  providerId: string
  modelId: string
  query: string
  mode: all | architecture
  topK: int
  minScore: float
  maxDepth: int
  maxNodes: int
  semanticHits: SemanticHit[]
  anchors: GraphAnchor[]
  graphEvidence: GraphEvidence[]
  truncated: bool
```

## FreshnessReport

```text
GraphRagFreshnessReport
  valid: bool
  status: current | stale | incompatible | unknown
  indexRevision: string
  currentRevision?: string
  repositoryMatches: bool
  providerMatches: bool
  modelMatches: bool
  dimensionsMatch: bool
  messages: string[]
```

Strict mode requires `valid=true` before query execution.

## Persistence

Default directory:

```text
engineering-graph/.graphrag/
  index.json
```

The single index file contains manifest + chunks for V4 simplicity. Writes use temporary sibling + atomic replace.
