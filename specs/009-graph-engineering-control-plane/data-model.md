# Data Model: Engineering Graph

## Canonical ownership

All graph records are derived from repository artifacts. Every node carries:

```text
repository      owner/name
canonicalId     globally unique within repository projection
sourcePath      repository-relative source when applicable
sourceRevision  Git SHA used for extraction
syncRunId       current synchronization run
```

No canonical specification prose is stored for editing in Neo4j. Small titles/status/line references may be projected for discovery.

## Node Labels

### Requirement

```text
canonicalId  SPEC-ID:FR-001 | SPEC-ID:SC-001
sourceId     FR-001 | SC-001
kind         functional | success_criterion
text         bounded requirement statement
critical     boolean
sourcePath   specs/.../spec.md
line         integer|null
```

### Spec

```text
canonicalId  SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE
featureId    009
slug         graph-engineering-control-plane
title
status
sourcePath   specs/009-.../spec.md
enforced     boolean
```

### ADR

```text
canonicalId  ADR-0017
number       0017
title
status
sourcePath   docs/adr/0017-....md
```

### Task

```text
canonicalId  SPEC-ID:T001
sourceId     T001
title
status       pending | done
priority     integer|null
parallel     boolean
userStory    string|null
phase        string|null
sourcePath   specs/.../tasks.md
line         integer|null
```

### CodeArtifact

```text
canonicalId  repository-relative path
path         repository-relative POSIX path
kind         source | config | docs | script | other
exists       boolean
```

### Test

```text
canonicalId  repository-relative path
path         repository-relative POSIX path
kind         unit | integration | e2e | storybook | architecture | other
exists       boolean
```

### PullRequest

```text
canonicalId  owner/name#13
number       integer
title
state        open | closed | merged | unknown
url          string|null
headSha      string|null
baseSha      string|null
source       git | github_event
```

## Core Relationships

```text
(Requirement)-[:REALIZED_BY]->(Spec)
(Spec)-[:CONSTRAINED_BY]->(ADR)
(Spec)-[:DECOMPOSED_INTO]->(Task)
(Spec)-[:DEPENDS_ON]->(Spec)
(Task)-[:DEPENDS_ON]->(Task)
(Task)-[:IMPLEMENTED_BY]->(CodeArtifact)
(Task)-[:VALIDATED_BY]->(Test)
(PullRequest)-[:IMPLEMENTS]->(Task)
(PullRequest)-[:CHANGES]->(CodeArtifact|Test)
```

Although the vocabulary contains eight relationship names, `DEPENDS_ON` is valid for both Spec→Spec and Task→Task and `CHANGES` can target CodeArtifact/Test.

Every relationship carries:

```text
repository
sourcePath|null
sourceRevision
syncRunId
provenance       explicit | convention | git | github_event
```

## Identity Rules

### Spec

```text
specs/007-opportunity-workflow
→ SPEC-007-OPPORTUNITY-WORKFLOW
```

### Requirement

```text
SPEC-007-OPPORTUNITY-WORKFLOW:FR-021
SPEC-007-OPPORTUNITY-WORKFLOW:SC-009
```

### Task

```text
SPEC-007-OPPORTUNITY-WORKFLOW:T040
```

### ADR

```text
docs/adr/0015-opportunity-domain-commands.md
→ ADR-0015
```

### Paths

CodeArtifact/Test canonical IDs are normalized repository-relative POSIX paths with no leading `./`.

### Pull Request

```text
az1nn/cpxlabs-admin#13
```

## Frontmatter Extension

Markdown MAY contain a leading YAML block:

```yaml
---
graph:
  id: SPEC-RBAC-001
  enforced: true
  depends_on:
    - SPEC-AUTH-001
  constrained_by:
    - ADR-0012
---
```

Task/spec explicit metadata may also provide:

```yaml
graph:
  implements:
    - apps/web/src/platform/authorization/authorization-provider.tsx
  validated_by:
    - apps/web/src/platform/data/data-provider.architecture.test.ts
```

Explicit metadata wins over convention for relationship creation but MUST still resolve to valid canonical targets.

## Sync Run Model

The database does not require a persistent `SyncRun` node in V1. `syncRunId` is generated per execution and stamped on all observed nodes/relationships.

Full sync algorithm:

1. discover repository revision;
2. parse all supported artifacts into an in-memory graph;
3. validate canonical uniqueness and explicit references before database writes;
4. initialize constraints;
5. MERGE nodes by `(repository, canonicalId)` per label;
6. MERGE relationships with deterministic endpoints/type;
7. stamp current `syncRunId`;
8. delete relationships for the repository not seen in the run;
9. detach-delete derived nodes for the repository not seen in the run;
10. emit deterministic counts/statistics.

`syncRunId` is operational metadata and is ignored by logical-idempotency tests.

## Validation Model

```text
InvariantResult
  rule
  severity: error|warning
  entity
  message
  sourcePath?
```

Rules are configured in `engineering-graph/config.yaml`; global validation exit code is non-zero iff at least one `error` result exists.

## Context Package

JSON shape:

```json
{
  "task": {},
  "spec": {},
  "requirements": [],
  "adrs": [],
  "dependencies": [],
  "code": [],
  "tests": [],
  "pullRequests": [],
  "budget": { "maxDepth": 3, "maxNodes": 80 }
}
```

Markdown is a deterministic rendering of the same package.

## Execution Plan

```json
{
  "ready": [],
  "blocked": [{"task":"...","blockedBy":[]}],
  "cycles": [],
  "conflicts": [{"left":"...","right":"...","artifacts":[]}],
  "waves": [["TASK-A","TASK-C"],["TASK-B"]]
}
```

The planner never changes source task status; `tasks.md` remains canonical.
