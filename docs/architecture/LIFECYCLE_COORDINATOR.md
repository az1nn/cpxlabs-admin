# Lifecycle Coordinator V10

V10 is the read-only coordination/projection layer above the existing V3–V9 Engineering Graph execution pipeline. It answers what lifecycle state is actually proven for one canonical Task and what single action is permitted next by the current evidence.

## Authority boundary

V10 does not advance lifecycle state. It has no authority to acquire/release leases, create/remove worktrees, start/stop agent processes, execute validation, commit/push/open/merge pull requests, edit Spec Kit Task state, or pass/waive Human Async Gates.

Git/Spec Kit remains canonical. V3–V9 files under `.execution/` remain derived. Human Async Gate evidence proves only its recorded human/external observation and freshness boundary. Neo4j remains a rebuildable projection and is not required for `lifecycle-status`.

## Evidence flow

```text
Git / Spec Kit                                             canonical
      |
      +--> V3 allocation / lease                           derived
      +--> V5 run + V6 supervisor                          derived
      +--> V7 validation                                   derived
      +--> V8 publication / PR                             derived + live PR inspection
      +--> human review / Human Async Gates                external/human evidence
      +--> V9 post-publication receipt                     derived
      |
      v
V10 LifecycleEvidence -> pure reducer -> LifecycleAssessment
                                      |- phase
                                      |- blockers
                                      |- exactly one nextAction
                                      `- continuation payload
```

Later evidence never backfills missing earlier authority. For example, runner success does not prove validation, publication does not prove merge, and merge does not prove canonical Task completion.

## Command

```bash
graph-engineering lifecycle-status \
  --task <CANONICAL-TASK-ID> \
  --json
```

Optional Human Async Gate evidence:

```bash
graph-engineering lifecycle-status \
  --task <CANONICAL-TASK-ID> \
  --human-gates .execution/human-gates.json \
  --json
```

Disable live PR inspection for a local-only view:

```bash
graph-engineering lifecycle-status \
  --task <CANONICAL-TASK-ID> \
  --no-pr-inspect \
  --json
```

When a V8 publication has an opened PR but live PR state is unavailable, V10 reports `published` with `nextAction=inspect_pr_state`; it never guesses merge state.

## Lifecycle phases

V1 uses the closed vocabulary:

`unallocated -> allocated -> running -> executed -> validated -> published -> awaiting_human -> merged -> reconciled -> finalized`

`blocked` is used for contradictory identity or failure/remediation states where proceeding through the normal next tier would be unsafe.

The assessment is intentionally not persisted as a canonical state machine. It is recomputed from current evidence each time.

## Identity safety

Every overlapping repository, Spec, Task, branch, worktree, source revision, run, validation, publication and PR identity is checked. Contradiction fails closed to `blocked / repair_evidence`.

A missing later artifact does not invalidate earlier proven evidence. It simply stops the reported phase at the furthest tier actually proven.

## Human Async Gates

Human Async Gate input follows `docs/ai/human-async-gates.md` and the Spec 018 JSON contract.

- required `PENDING` -> `await_human_gate`;
- required `FAILED` -> `remediate_human_gate`;
- required stale `PASSED`/`WAIVED` -> treated as unresolved for the current HEAD;
- fresh externally recorded `PASSED`/`WAIVED` -> accepted only for that recorded observation.

V10 never changes gate status. Automated green evidence never passes a distinct human gate.

## Read-only guarantee

The coordinator uses existing read helpers for leases, runs, supervisor jobs, validation records, publication records and V9 receipts. Live PR inspection is `gh pr view ... --json ...` with argv execution and `shell=False`.

The status path does not call save/release/remove/start/stop/validate/publish/fetch/merge APIs and writes no `.execution/`, Git, GitHub or Neo4j state.

## Continuation payload

Every assessment includes derived continuation context containing repository, base, branch, PR when known, HEAD, Spec/Task identity, automated evidence summary, unresolved Human Async Gates, the exact `nextAction`, freshness instructions and the V10 authority boundary.

The continuation payload is convenience context only. The next session must re-check Git, PR and gate freshness before acting.

See ADR-0026 and `specs/018-lifecycle-coordinator/contracts/lifecycle-assessment.md`.