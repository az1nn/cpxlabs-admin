# CPXLABS Admin — ChatGPT Project Instructions

Repository: `https://github.com/az1nn/cpxlabs-admin`

These instructions are intended to be mirrored into the ChatGPT Project Instructions for CPXLABS Admin. The repository copy is the reviewable/versioned source; ChatGPT UI settings are an execution mirror only.

## Canonical authority

For repository-related work, treat Git-backed code, Spec Kit artifacts, ADRs, tests, and Git history as canonical.

Neo4j Engineering Graph data, ContextPackages, execution manifests, `SESSION_HANDOFF.md`, and chat history are derived context only. They may accelerate navigation and continuity but never override canonical Git-backed state.

## Session bootstrap

At the beginning of a material development session:

1. refresh repository, base branch, active branch, PR, and relevant Spec Kit state;
2. read `AGENTS.md`;
3. follow `docs/ai/context-handoff.md`;
4. reconstruct only the bounded context required for the current task;
5. when available, refresh and validate Engineering Graph context before relying on generated packages.

Do not load the entire repository or replay previous chats by default.

## Context health

Continuously monitor whether the current conversation remains a trustworthy working context, but do not report status on every response.

Use:

```text
GREEN   context is coherent; continue normally
YELLOW  a semantic boundary is approaching; finish the current safe atomic step
RED     continuing materially increases stale/conflicting-context risk
```

Conversation length, message count, or number of tool calls alone must never trigger a handoff.

Potential boundaries include:

- feature, milestone, Spec Kit phase, or coherent PR group completed;
- a materially different workstream is about to start;
- branch, PR, spec, ADR, or task state is becoming difficult to distinguish;
- old logs, diffs, experiments, or failed approaches dominate useful context;
- settled questions begin being re-asked;
- repository state has advanced enough that chat history is no longer a trustworthy implementation snapshot;
- stale ContextPackages, graph projections, plans, or prior verification evidence risk being reused after HEAD changes.

When RED, explicitly say:

> ⚠️ **Context boundary recommended — good moment to start a new chat.**

Do not abandon a safe atomic action already in progress. Finish or explicitly stop the current step first.

Then generate a `SESSION_HANDOFF.md` following `docs/ai/session-handoff-template.md`.

## Handoff contract

The handoff must describe final state, not conversation history, and include:

- objective;
- repository/base/branch/HEAD;
- PR/issue when applicable;
- active Spec Kit feature/task state;
- final decisions;
- superseded decisions that must not be reused;
- completed work;
- canonical artifacts;
- Engineering Graph/ContextPackage references worth refreshing;
- verification state and freshness boundary;
- open items/blockers;
- exact Next Action;
- minimum bootstrap context for the next chat.

Never paste full transcripts, long logs, or speculative history into the handoff.

## Freshness and safety

A new chat must verify freshness before acting.

At minimum, verify:

1. current `master` / target base;
2. active branch and expected HEAD;
3. PR/issue state;
4. active Spec Kit artifacts/tasks;
5. relevant ADRs and source files;
6. Engineering Graph state when used;
7. whether generated ContextPackages and previous verification evidence still match current Git revision.

If a handoff conflicts with Git, Spec Kit, ADRs, code, tests, or current PR state, canonical repository state wins and the mismatch must be called out.

Changing chats never resets project lifecycle, validation requirements, task dependencies, PR ownership, or CI expectations.
