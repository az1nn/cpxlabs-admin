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
- Never cross an explicit human gate automatically.
- Never delete context required to reconstruct decisions.
- When sources conflict, current canonical state wins.

## Human gates

When a decision is explicitly reserved to the user, finish every other verifiable action first and stop only at that decision boundary.

Examples:

- Design Gate;
- visual approval;
- manual merge authorization;
- architectural decision;
- production release;
- cost approval;
- destructive change.

Present exactly:

- current state;
- evidence;
- decision required;
- effect of each relevant alternative.

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
