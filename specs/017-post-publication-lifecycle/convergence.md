# Convergence: Post-Publication Lifecycle V9

**Feature**: `SPEC-017-POST-PUBLICATION-LIFECYCLE`  
**Implementation anchor**: `5da98ef88e0adba778de261a1d6cdbd4b6da3467`  
**Status**: Converging — implementation/policy complete; final freeze gates pending

## Conclusion

V9 closes the lifecycle after V8 publication without collapsing distinct authority tiers.

```text
V8 pr_opened
    |
human review / merge
    |
    v
V9 reconcile
  |- PR merged
  |- merge reachable from refreshed base
  |- canonical Task already checked complete
  |- publication / lease identity valid
    |
explicit finalize
  |- release matching lease
  + optional remove matching clean worktree
```

PR merge, canonical Task completion and cleanup intent remain separate facts.

## Delivered behavior

- versioned derived `PostPublicationReceipt`;
- read-only post-publication reconciliation;
- exact V8 publication identity validation;
- `gh pr view` merged-state/merge-SHA evidence through argv + `shell=False`;
- refreshed configured base branch;
- merge ancestry verification;
- canonical Task lookup from merged base using `git show`;
- exact-one checked Task requirement;
- explicit lease release;
- additionally explicit clean-worktree removal;
- no V9 force-delete path;
- idempotent partial-finalization recovery;
- `post-publication-status` / `post-publication-finalize` CLI surfaces;
- project-owned Continuation Prompt policy/template;
- Human Async Gate policy/schema/freshness semantics;
- handoff and Engineering Graph agent-policy integration;
- V9 architecture and operator documentation.

## Authority convergence

PASS.

V9 has no code path to:

- approve/merge/close a PR;
- enable auto-merge;
- mark a Spec Kit Task complete;
- derive Task completion from process/validation/publication success;
- force-remove a dirty worktree;
- delete remote branches;
- project lifecycle receipts into Neo4j canonical truth.

## Recovery convergence

PASS at the implementation anchor.

A deliberately added retry test exposed a real edge case: after lease release succeeded and dirty-worktree removal failed, retry incorrectly demanded an active lease again. The correction persists phase authority in the receipt:

- `leaseReleased=true` prevents double release;
- only the already-satisfied missing-active-lease condition is neutralized;
- PR merge, merge ancestry and canonical Task evidence are still revalidated;
- cleanup remains fail-closed for dirty/unregistered worktrees.

Engineering Graph #372 passed the corrected core.

## Project-memory convergence

PASS.

Repository-owned project instruction sources now require a Continuation Prompt for every material pause/handoff/wait where work remains.

The prompt includes repository/base/branch/PR/HEAD/Spec, automated gate state, unresolved Human Async Gates, one exact Next Action, freshness instructions and the current authority boundary.

Prompt state is explicitly derived/non-authoritative and must be regenerated after relevant state changes.

## Human Async Gate convergence

PASS as a documented operating contract.

- schema and statuses are explicit;
- `PENDING` required gates block readiness/completion claims;
- `WAIVED` requires human rationale;
- agents cannot self-pass/self-waive;
- CI does not implicitly pass a separate human gate;
- human acceptance does not replace automated tests;
- automated CI that is merely running remains an automated pending gate, not a Human Async Gate unless human/external acceptance is genuinely required.

Spec 017 currently requires no Human Async Gate because this toolchain change has deterministic repository/CI coverage and no deployment/device/manual observation requirement.

## Compatibility evidence

At implementation anchor `5da98ef8…`, Engineering Graph #372 passed:

- offline V1–V9 unit/integration suite;
- runtime dependency isolation;
- Neo4j schema/sync/idempotency/validation;
- V1 graph query gates;
- V2 ContextPackage gates;
- V3 Execution Graph gates;
- V4 GraphRAG gates;
- existing V5–V8 regression coverage.

The final documentation/policy commits change HEAD, so this is an implementation anchor rather than final freeze evidence.

## Final freeze rule

Before PR #25 becomes Ready for Review:

1. reconcile T001–T050 against actual evidence;
2. run Spec Kit on the resulting final HEAD;
3. run Engineering Graph on that exact same HEAD;
4. run Product CI on that exact same HEAD;
5. verify no required Human Async Gate is `PENDING`;
6. mark T051–T054 complete only after those conditions hold;
7. do not create another content commit after the accepted freeze HEAD; put final run IDs in PR metadata/body instead.
