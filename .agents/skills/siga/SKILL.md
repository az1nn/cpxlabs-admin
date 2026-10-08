---
name: siga
description: Reconcile the real persistent state of an existing app, project, or workstream and continue from the correct boundary. Trigger whenever the user says "Siga" as a standalone instruction, or explicitly invokes the SIGA continuation protocol. Never interpret SIGA as a generic request to merely do the next thing.
---

# SIGA — Portable Continuation Protocol

## Core meaning

"SIGA" means:

> Descubra onde realmente estamos e continue corretamente dali.

Never treat it as:

> Apenas execute alguma próxima coisa.

Operate in **VERIFY-FIRST** mode.

Trust sources in this order:

**REAL STATE > HANDOFF > MEMORY > CHAT**

The current verifiable system state is canonical. A handoff is only the last known hypothesis.

## Canonical skill source

This repository-owned file is the **single procedural source of truth for SIGA**.

- Do not create or maintain a second SIGA skill copy in ChatGPT app state, Library, Project settings, memory, another local registry, or any parallel knowledge store.
- Memory and chat may retain only a pointer/behavioral reminder that this repository skill must be read and followed; they must not become an independent SIGA specification.
- When the repository skill and remembered/chat wording differ, verify the repository version and follow the repository skill.
- Evolve SIGA by editing this repository skill through the normal repository workflow rather than synchronizing multiple copies.
- Per-workstream handoffs remain allowed: they record project state/delta, not a second definition of the SIGA protocol.


## 1. RECONCILE

Before doing new work, reconstruct the current state from every relevant source that is actually available.

Depending on the environment, inspect the equivalents of:

- app/project/workspace state;
- branch, workspace, environment, deployment, or active version;
- current HEAD/revision/version;
- open tasks, issues, PRs/MRs, cards, jobs, runs, agents, or workers;
- CI/CD, tests, lint, typecheck, builds, deploys, previews, health checks;
- reviews, comments, approvals, human gates, pending decisions;
- blockers, failures, logs, artifacts, specs, ADRs, checklists, handoffs;
- remote state versus local state.

Do not assume the last chat message is still true.

If canonical state cannot be reached, use the strongest persistent source available, state the limitation, and do not invent current status.

## 2. CLASSIFY

After reconciliation, choose **exactly one** mode.

### MODE A — RESUME

Use when work was started but is not yet complete and there is actionable unfinished work.

Examples:

- incomplete implementation;
- unresolved bug;
- unfinished task/spec;
- local or branch changes not finalized;
- failure already produced by a completed validation;
- work interrupted between implementation and verification.

Action:

Continue from the last safe boundary. Do not create a redundant new workstream.

### MODE B — WATCH

Use when the main work has already been dispatched and there is still a genuinely active process or pending validation/gate.

Examples:

- CI still running;
- agent/worker still running;
- deploy in progress;
- review or explicit human gate pending;
- async validation still executing.

Action:

Do not duplicate work. Inspect current status, consume completed results, and correct completed failures when possible.

If an active process finishes and exposes actionable corrective work, reclassify on the next cycle before acting.

Never open a parallel branch, PR, task, session, or job merely because the existing one has not finished.

### MODE C — ADVANCE

Use only when the previous work is verifiably complete and there is no active execution or pending gate that still belongs to it.

Action:

Derive the next logical unit from the roadmap, spec, tasks, issues, handoff, dependencies, and explicitly stated priorities.

Only in this mode may a new branch, PR, task, spec, or workstream be started.

## 2A. Concurrency, ownership and collision fencing (mandatory)

SIGA may be invoked concurrently by multiple chats, agents, terminals or CI workers. **Reconciliation is not a lock.** A green CI, an empty PR list or a clean default branch never proves that an unfinished feature branch is available for another writer.

### Identify the protected scope

Before any mutation, identify:

- repository + workstream/spec/task identity;
- exact base and feature branch and their freshly observed HEADs;
- affected paths, shared generated artifacts and dependent tasks;
- observable owner/run/session, active processes, pending PRs and remote updates;
- worktree and lease state wherever the execution environment exposes it.

A branch with incomplete spec/tasks and recent commits is an unfinished execution even without a PR or CI run. Treat rapidly moving or ambiguously owned scope as potentially active. If there is a credible active writer on an overlapping scope, **classify WATCH for that scope** and do not start a second writer, branch, PR, job or implementation. Read-only inspection and a collision handoff are allowed.

### Single-writer rule and parallel waves

**At most one mutating owner per overlapping task, branch or artifact set.** Parallel execution is allowed only for explicitly dependency-ready, conflict-free tasks with separate worktrees/branches and non-overlapping files/generated outputs. A shared integration point, contract, migration, CI workflow or handoff file creates a collision edge until ownership is delegated or the tasks are serialized.

A domain specialist may implement in its domain, but ownership of the affected result must remain with the designated domain owner. Orchestrator owns scheduling and handoffs, not the ability to bypass these conflicts. Work that cannot prove independent ownership is serialized.

### Leases: local versus distributed

- The Engineering Graph V3 `execution-prepare` worktree/lease registry protects allocation **only within its local orchestrator checkout**. It is **not** a distributed cross-chat/cross-host mutex. Never present a local lease or an ordinary issue/label/comment as proof of exclusive remote ownership.
- Where a shared coordinator is actually deployed, acquire an **atomic compare-and-set or transactional** scoped lease before mutation. Record a unique owner/run ID, scope, fencing generation/token, current revision and expiry/heartbeat. Reject second acquisitions of an overlapping active scope. Validate ownership and fencing generation on every write; expiry alone does not authorize a stale writer to keep writing. Release only the owned lease after a final state check.
- Where no such distributed coordinator exists, **do not claim a remote lock exists**. Adopt a conservative single-writer policy: sessions seeing current/ambiguous overlapping work remain read-only WATCH; an uncontended owner may resume after fresh reconciliation, but this is cooperative safety, not globally guaranteed exclusivity.

### Every-write freshness and collision response

Before updating any remote/shared branch or file:

1. Re-read its current revision and compare it with the revision observed when selecting the work.
2. Use conditional writes where supported (file blob SHA, ref expected SHA / force-with-lease, server-side compare-and-set). Write only to the owned feature branch; never blind-write to the default branch.
3. On a failed condition, unexpected HEAD movement, ownership loss, newly discovered overlap or stale package: **STOP writes immediately**. Reconcile the competing changes, classify WATCH or RESUME as warranted and preserve both sides.
4. Do not force-push, replace an unrelated file, delete another worker's worktree/lease, auto-close a competing PR or silently rerun the same task. Do not retry a failed conditional write without a full re-read and ownership decision.
5. Before merge, re-check base and feature HEADs, actual mergeability, required exact-head gates and absence of unresolved ownership/human gates. A successful build on an older commit is not evidence for the new HEAD.

GitHub Actions `concurrency` groups can cancel or serialize redundant **CI runs**, but they do not lock development sessions, branches or file writes. Treat CI serialization and task ownership as separate controls.

### Handoff of contention

Keep the existing CAVEMAN HANDOFF structure; record scope, observed owner (or unknown), branch/base HEADs, lease type (distributed/local/none), paths in contention, active process/check state and next safe action under VERIFY, GATES, BLOCKERS and NEXT. A stale or abandoned scope is not released by guessing elapsed time: prove termination or obtain explicit authorized recovery, preserve unmerged changes and fence out the old writer first. If this cannot be proven, stop at a human ownership gate rather than inventing successful recovery.

## 3. EXECUTE

After selecting the mode:

**implement → verify → classify → persist**

Verification depth must match the environment and use the strongest evidence available.

Examples:

- tests;
- lint;
- typecheck;
- build;
- CI;
- Engineering Graph;
- preview;
- screenshots;
- API checks;
- queries;
- logs;
- deploy health;
- human validation;
- contract validation.

Context compression must never reduce verification rigor.

## Invariants

During SIGA execution:

- Never mask FAIL.
- Never declare success without evidence.
- Never duplicate work already in progress.
- Never create a new workstream before reconciling the existing one.
- Never trust chat history over canonical state.
- Never change behavior merely to make a gate green without resolving the underlying cause.
- Never cross an explicit human gate automatically unless a standing operator authorization explicitly covers that gate and all stated preconditions are freshly verified.
- Never delete context required to reconstruct decisions.
- When sources conflict, current canonical state wins.

## Human gates

When a decision is explicitly reserved to the user, finish every other verifiable action first and stop only at that decision boundary.

Examples:

- Design Gate;
- visual approval;
- manual merge authorization when no standing merge authorization exists;
- architectural decision;
- production release;
- cost approval;
- destructive change.

Present exactly:

- current state;
- evidence;
- decision required;
- effect of each relevant alternative.

### Standing merge authority — this repository

Effective 2026-09-24, the operator grants SIGA standing authority to resolve PR branch conflicts and merge without asking for additional confirmation when all of the following are true:

- the exact PR/repository/base/head identity has been freshly reconciled from real state;
- any branch conflict has been resolved against the current base without masking or discarding unrelated changes;
- every required automated test/check/gate for the resulting exact HEAD has passed;
- no separate required human/manual acceptance gate remains PENDING;
- repository protections/rulesets permit the merge.

Before merging, re-check mergeability and the exact HEAD. Use expected-head protection when the platform supports it. After merging, verify the PR is actually merged and the base contains the merge result.

This standing authority does **not** authorize bypassing branch protection, force-pushing over concurrent work, suppressing failed checks, self-waiving unrelated human gates, or declaring success from stale evidence.

## Durable handoff

At a natural session boundary, persist one compact handoff.

Use this exact structure:

```text
CAVEMAN HANDOFF v1

APP:
WORKSTREAM:
STATE:
MODE:
CANONICAL SOURCE:

CURRENT VERSION / HEAD:
BASE:
BRANCH / ENV:
PR / MR / TASK:
SPEC / ADR:

DONE:
VERIFY:
GATES:
BLOCKERS:

INVARIANTS:
NEXT:

VERIFY-FIRST:
<minimum instructions required to reconstruct the real state on the next run>
```

The handoff records state and delta, not a narrative transcript.

It must be sufficient for another agent, chat, or app to resume without depending on prior conversation history.

## Next session behavior

On the next standalone `Siga`:

1. locate the latest persisted handoff available;
2. run VERIFY-FIRST again against the real system;
3. reconcile differences;
4. classify RESUME, WATCH, or ADVANCE;
5. continue from the verified boundary.

The handoff never overrides the live system.

## Portability

SIGA is not Git-specific.

Map the same semantics onto the environment:

- GitHub/GitLab: branch → PR/MR → CI → review → merge;
- Canva: design → comments → approval → export;
- Trello: board → card → checklist → blockers;
- Notion: spec → tasks → decisions → status;
- SaaS: workspace → jobs → state machine → logs;
- Infra: environment → deployment → health → incidents;
- Agents: run → child agents → outputs → pending actions.

The invariant flow is always:

**RECONCILE → CLASSIFY → EXECUTE → VERIFY → HANDOFF**
