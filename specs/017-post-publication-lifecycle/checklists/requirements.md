# Requirements Checklist — Post-Publication Lifecycle V9

## Authority

- [x] V9 requires an existing V8 publication record.
- [x] Human review/merge remains outside V9 authority.
- [x] Canonical Task completion is read from Git-backed Spec Kit state, never inferred from runtime/publication state.
- [x] Lease release and worktree cleanup require explicit operator intent.
- [x] Dirty worktrees are never force-removed by V9.

## Reconciliation

- [x] PR merge evidence is required.
- [x] Merge commit reachability from refreshed base is required.
- [x] Publication/lease/repository/task identity must match.
- [x] Canonical Task entry must exist exactly once and be checked complete.
- [x] Finalization is idempotent.

## Project memory

- [x] Continuation Prompt is required on pause/handoff/external wait.
- [x] Continuation Prompt includes repo/base/branch/PR/HEAD/spec/gates/next action/freshness.
- [x] Stale prompts are non-authoritative and must be regenerated.

## Human Async Gates

- [x] Human/external asynchronous tests use an explicit gate contract.
- [x] Required PENDING gates block final readiness/completion claims.
- [x] CI cannot implicitly satisfy a distinct human gate.
- [x] WAIVED requires human rationale.
- [x] Gate evidence is review evidence, not a replacement for automated regression coverage.

## Quality

- [x] V1–V8 compatibility is mandatory.
- [x] Product runtime isolation remains mandatory.
- [x] Final freeze requires Spec Kit + Engineering Graph + Product CI green on one HEAD.
