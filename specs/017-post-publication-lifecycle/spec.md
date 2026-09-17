# Feature Specification: Post-Publication Lifecycle V9

**Feature ID**: `SPEC-017-POST-PUBLICATION-LIFECYCLE`

## Objective

Close the lifecycle after a V8-published pull request is merged, while preserving human authority over merge/completion decisions and making asynchronous human validation explicit.

V9 reconciles merged publication evidence with canonical repository state. It may only clean derived execution state after proving that the merged base already contains the canonical Task completion. It must never infer Task completion from process exit, validation success, publication success, or PR merge alone.

The project must also persist a continuation policy: whenever work pauses, hands off, or waits on an asynchronous/human gate, the agent generates an exact prompt for the next continuation step.

## Authority model

```text
V7 validation passed
      |
V8 publication / PR opened
      |
      v
human review + merge
      |
      v
V9 reconciliation
  |- verify PR merged
  |- verify merge is reachable from base
  |- verify canonical Task is already complete in base
  |- verify active lease/publication identity
  |- optional lease release
  |- optional clean worktree removal
  |- emit lifecycle receipt + continuation prompt
```

V9 does not approve or merge PRs, edit canonical Task state from derived runtime evidence, force-delete dirty worktrees, or bypass pending human gates.

## Functional requirements

- **FR-001** V9 MUST consume one terminal V8 publication record with `status=pr_opened`.
- **FR-002** V9 MUST verify repository, Task, Spec, branch, publication, and active lease identity before cleanup.
- **FR-003** V9 MUST inspect the published PR through explicit GitHub CLI argv with `shell=False`.
- **FR-004** V9 MUST require the PR state to be merged before any lease/worktree mutation.
- **FR-005** V9 MUST resolve the PR merge commit and verify it is reachable from the configured base branch.
- **FR-006** V9 MUST refresh the base branch before evaluating canonical completion.
- **FR-007** V9 MUST locate the canonical Task in the merged base Spec Kit `tasks.md` and require it to be checked complete.
- **FR-008** V9 MUST fail closed when the canonical Task is absent, ambiguous, or incomplete.
- **FR-009** V9 MUST never change a Task checkbox as a consequence of runtime/publication state.
- **FR-010** V9 MUST support a read-only reconcile/status operation before any cleanup action.
- **FR-011** Lease release MUST require explicit operator intent.
- **FR-012** Worktree removal MUST require explicit operator intent in addition to lease-release intent.
- **FR-013** Dirty worktrees MUST never be removed by the normal finalize path.
- **FR-014** V9 MUST persist a versioned derived lifecycle receipt under `.execution/`.
- **FR-015** Lifecycle receipts MUST record publication ID, PR URL/number, merge commit, base branch, canonical completion evidence, cleanup actions, timestamps, and final state.
- **FR-016** Re-running reconciliation/finalization MUST be idempotent and must not double-release leases or remove unrelated worktrees.
- **FR-017** V9 MUST expose `post-publication-status` and `post-publication-finalize` through the standard `graph-engineering` entrypoint.
- **FR-018** CLI output MUST support JSON and human-readable forms.
- **FR-019** V9 MUST preserve the V1–V8 product/runtime isolation boundary.
- **FR-020** V9 MUST not project lifecycle receipts into Neo4j canonical truth.

## Continuation-memory requirements

- **FR-021** Repository-owned ChatGPT Project Instructions MUST require a `Continuation Prompt` whenever work pauses, hands off, or is blocked on an external/asynchronous result.
- **FR-022** The continuation prompt MUST include repository, base, branch, PR, HEAD, active Spec, gate state, exact next action, and freshness instruction.
- **FR-023** The session handoff template MUST contain a dedicated `Continuation Prompt` section.
- **FR-024** The continuation prompt MUST be regenerated after HEAD/PR/gate state changes; stale prompts are not authoritative.

## Human async gate requirements

- **FR-025** Tests/checks whose result depends on later human observation or external asynchronous completion MUST be represented as explicit Human Async Gates.
- **FR-026** A Human Async Gate MUST record: Gate ID, subject, trigger/evidence, expected observation, approver, status, next action, and freshness boundary.
- **FR-027** Allowed statuses are `PENDING`, `PASSED`, `FAILED`, and `WAIVED`; waiver requires human rationale.
- **FR-028** Automated CI success MUST NOT implicitly satisfy a separate Human Async Gate.
- **FR-029** An agent MUST NOT claim merge/readiness/completion when a required Human Async Gate is still `PENDING`.
- **FR-030** Required Human Async Gates MUST be surfaced in PR/handoff evidence and in the continuation prompt.
- **FR-031** Human Async Gate evidence is operational/review evidence, not a replacement for automated tests or canonical code/spec state.

## Success criteria

- **SC-001** A merged V8 PR with canonical Task already complete can be reconciled without mutating canonical Task content.
- **SC-002** An open/unmerged PR is rejected before cleanup.
- **SC-003** A merged PR whose Task is not canonically complete is rejected and produces a continuation path instead of silently completing it.
- **SC-004** Merge commit reachability against the base branch is verified.
- **SC-005** Explicit finalize can release one matching lease and optionally remove one clean matching worktree.
- **SC-006** Dirty worktree cleanup fails closed.
- **SC-007** Repeated finalize is idempotent and does not affect unrelated allocations.
- **SC-008** Project instructions/handoff template always expose a reusable continuation prompt contract.
- **SC-009** Human Async Gate documentation prevents required asynchronous/manual validation from being represented as automatically complete.
- **SC-010** Spec Kit, Engineering Graph and Product CI remain green on the final freeze HEAD.

## Out of scope

- automatic PR approval or merge;
- auto-merge enablement;
- editing Task checkboxes based on runtime/publication state;
- force deletion of dirty worktrees;
- deleting remote branches;
- release/deployment automation;
- remote/distributed cleanup;
- treating human observations as substitutes for automated regression tests.
