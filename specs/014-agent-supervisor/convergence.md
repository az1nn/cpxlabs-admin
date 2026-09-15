# Convergence: Agent Supervisor V6

## Decision

The V6 implementation is feature-complete and is entering freeze. No material requirement remains unresolved.

## Implemented surface

- versioned `SupervisorJob` / `SupervisorTask` derived state;
- active V3 allocation and manifest revision/repository/agent checks;
- exact task ownership through job-owned V5 `runId` history;
- deterministic wave-order launches;
- bounded `maxParallel` concurrency;
- bounded `maxAttempts` retry policy;
- retries only for `failed` / `orphaned`;
- no automatic retry after `stopped`;
- idempotent tick behavior while slots are occupied;
- `settled` terminal scheduling observation;
- fail-closed supervisor stop ownership check delegated to V5 process safety;
- CLI start/tick/status/stop surfaces with JSON output;
- architecture/quickstart documentation and ADR-0022.

## Authority invariants preserved

V6 does not:

- mark Spec Kit Tasks complete;
- edit canonical specs/tasks/code;
- execute validation commands as completion authority;
- release V3 leases or remove worktrees;
- commit/push/open/review/merge pull requests;
- create semantic/canonical Neo4j edges from runtime observations;
- become a product-runtime dependency.

A V5 exit code `0` maps only to supervisor task `succeeded`. A supervisor job `settled` means only that its configured local scheduling policy has no pending/running/retryable work.

## Validation evidence before freeze-candidate closure

Implementation candidate: `d4d9ad4c9918047bc9f4071e3d85dacc1e4ab42f`

- Spec Kit #382 — **success**
- Engineering Graph #314 — **success**
- Product CI #715 — **success**

Engineering Graph #314 executed the full Python unittest/integration discovery, application-runtime isolation guard, Neo4j sync/idempotency/validation, V1–V5 smokes and the new V6 supervisor tests.

## Final freeze rule

The commit containing this convergence record and the final SC-002/SC-004 test assertions is the V6 freeze candidate. PR #22 is ready for review only after **Spec Kit + Engineering Graph + Product CI are all green on that exact freeze-candidate HEAD**. No source/spec/test change may be made afterward without invalidating the freeze and rerunning all three domains.

## Deferred intentionally

The following remain future specs/ADRs:

- automatic validation-command execution and interpretation;
- automatic lease release/worktree cleanup;
- autonomous commit/push/PR/review/merge;
- remote/distributed agent execution;
- cross-repository/global priority scheduling;
- runtime/supervisor state projection into Neo4j;
- a resident daemon (which may later invoke the same tick primitive).
