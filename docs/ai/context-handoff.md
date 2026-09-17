# Context Handoff Policy

This policy defines when an AI-assisted development conversation should remain in the current chat and when it should recommend a clean handoff to a new chat.

The goal is not to maximize chat length. The goal is to preserve correctness, traceability, and low-noise working context.

## Authority

Git-backed artifacts remain canonical: `.specify/`, `specs/`, `docs/adr/`, source code, tests, and Git history.

Conversation history, generated handoffs, Engineering Graph projections, ContextPackages, execution manifests, lifecycle receipts, Continuation Prompts, and agent-specific adapters are derived operational context. They may summarize canonical state, but they never override it.

Human Async Gate evidence is review/acceptance evidence bound to a specific freshness boundary. It does not replace Git-backed source or required automated tests.

## Context health

Agents should continuously assess conversation context without printing a status on every response.

Three states are used:

- **GREEN** — current chat remains coherent; continue normally.
- **YELLOW** — a natural handoff boundary is approaching; finish the current atomic step, then consider a handoff.
- **RED** — continuing in the current chat materially increases the risk of stale or conflicting context; recommend a new chat before starting another substantial unit of work.

Only surface YELLOW or RED when there is a concrete reason. Never warn merely because the chat is visually long or has many messages.

## Handoff signals

A handoff becomes appropriate when one or more of these signals are material:

1. a feature, milestone, Spec Kit phase, or coherent PR group has completed;
2. the next requested task belongs to a materially different workstream;
3. current-state decisions are becoming mixed with superseded approaches;
4. the agent starts re-asking settled questions or confusing branches, PRs, specs, ADRs, or task state;
5. logs, diffs, failed attempts, screenshots, or old tool output dominate the useful working context;
6. substantial new work would require repeatedly reconstructing the same canonical state from earlier messages;
7. repository state has moved enough that conversation state is no longer a reliable implementation snapshot;
8. a clean boundary would allow a bounded Engineering Graph ContextPackage or Spec Kit scope to represent the next unit of work more precisely;
9. work is waiting on external/asynchronous evidence or a Human Async Gate and a clean continuation prompt is safer than keeping stale execution context alive.

## Preferred boundaries

Prefer handoffs at semantic boundaries rather than arbitrary token/message counts:

- PR or related PR set completed;
- feature slice completed;
- Spec Kit specification or implementation phase completed;
- milestone reached;
- architecture decision frozen;
- workstream change;
- release or deployment boundary;
- transition from research/design to implementation, or implementation to validation, when the prior phase contains substantial discarded exploration;
- an asynchronous/manual acceptance boundary where further action is impossible until a gate resolves.

Do not force `one chat = one PR`. Several tightly related PRs may belong to one coherent conversation.

## Continuation Prompt

Every material development update that leaves further work possible must provide a ready-to-paste Continuation Prompt, whether or not a full chat handoff is required.

The prompt must contain current repository/base/branch/PR/HEAD/Spec Kit state, automated gate state, unresolved Human Async Gates, one exact Next Action, freshness instructions, and the relevant authority boundary.

If state changes after the prompt is generated, regenerate it. A stale prompt is never authoritative over Git/PR/CI state.

## Human Async Gates

Follow `docs/ai/human-async-gates.md`.

Required Human Async Gates must be recorded explicitly in the handoff when present. A required `PENDING` gate blocks claims of final readiness/completion. Green CI does not automatically satisfy a separate human gate, and the agent may not self-approve/waive one.

Purely automated async CI that is still running should be recorded as an automated pending gate; it becomes a Human Async Gate only when human/external acceptance is required.

## Required behavior

When context reaches RED, the agent must say:

> ⚠️ **Context boundary recommended — good moment to start a new chat.**

Before recommending the switch, complete any safe atomic action already in progress when doing so avoids leaving repository state half-written.

Then generate a `SESSION_HANDOFF.md` using `docs/ai/session-handoff-template.md`.

The handoff must describe the final state, not replay the conversation. Superseded decisions must be explicitly marked invalid for continuation. It must also include current automated/Human Async Gate state and a reusable Continuation Prompt.

## New-chat bootstrap

Use the handoff's generated Continuation Prompt rather than a generic message. At minimum it must instruct the new chat to validate freshness before editing and continue from the exact `Next Action`.

The new chat must re-read canonical artifacts needed for the task. It must not assume that the handoff or prompt is fresher than Git.

## Interaction with Engineering Graph

When the Engineering Graph is available, a new chat should prefer a fresh bounded ContextPackage for the next READY task/spec rather than importing broad historical context.

Recommended sequence:

1. synchronize and validate the graph;
2. generate the task/spec ContextPackage;
3. validate strict freshness immediately before implementation;
4. read canonical paths referenced by the package;
5. verify automated and Human Async Gate state;
6. use `SESSION_HANDOFF.md` only for cross-session continuity that is not already represented by canonical artifacts;
7. regenerate derived context and Continuation Prompt after Git revision, graph evidence, PR state, CI state, or gate state changes.

## Validation rule

A handoff is successful when a fresh chat can answer all of the following without relying on the previous conversation transcript:

- What is the current objective?
- What is already complete?
- Which branch/PR/spec is active?
- Which decisions are authoritative?
- Which prior approaches are superseded?
- What automated gates are complete or pending?
- Which Human Async Gates are pending/failed/passed/waived and to what freshness boundary?
- What remains open?
- What is the exact next action?
- Which canonical files must be read before editing?
- What ready-to-paste prompt should be used to continue?

If those answers are ambiguous, the handoff is incomplete.
