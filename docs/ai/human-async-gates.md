# Human Async Gates

Human Async Gates make asynchronous/manual acceptance evidence explicit in AI-assisted engineering work.

They are used when a required result cannot be synchronously and deterministically asserted by the current automated workflow. Examples include a later production smoke, external propagation, human visual acceptance, a delayed provider callback, or a manual device/browser observation.

## Evidence classes

Automated CI and Human Async Gates are separate evidence classes.

- Automated CI proves what its scripts/assertions actually test.
- Human Async Gates prove an explicitly stated human/external observation.

A green CI run never implicitly marks a distinct human gate as passed. A passed human gate never replaces required automated tests.

## Required schema

Every Human Async Gate must include:

```text
Gate ID: HAG-###
Subject: <what is being validated>
Trigger / evidence: <run, URL, deploy, artifact, build, timestamp>
Expected observation: <concrete pass condition>
Approver: <human role/person>
Status: PENDING | PASSED | FAILED | WAIVED
Rationale: <required for WAIVED; optional otherwise>
Freshness boundary: <HEAD/build/deploy/version this applies to>
Next action: <exact action after resolution>
```

## Status semantics

### PENDING

The observation has not yet been completed or recorded. If the gate is required, the agent must not claim final readiness, merge readiness, release readiness, or completion.

### PASSED

A human/external observation met the expected condition for the recorded freshness boundary.

### FAILED

The expected observation did not hold. The next action must be remediation/retest rather than pretending the gate is satisfied.

### WAIVED

A human explicitly decided not to require the observation. A rationale is mandatory. Agents must never self-waive a required gate.

## Freshness

Human gate evidence is revision/build/deployment bound. If the relevant HEAD, artifact, deployment, configuration, or environment changes materially, the prior gate must be treated as stale and returned to `PENDING` unless the recorded observation remains demonstrably applicable.

## Required agent behavior

When a Human Async Gate exists, the agent must:

1. show the gate in PR/handoff evidence when it materially affects readiness;
2. keep required `PENDING` gates visible;
3. never silently convert automated success into human approval;
4. never self-mark a human gate `PASSED` or `WAIVED` without actual human/external evidence;
5. include unresolved gates in the Continuation Prompt;
6. regenerate the Continuation Prompt after gate status or freshness changes.

## Human Merge Gate

A Human Merge Gate is a Human Async Gate specifically tied to merge/release authority.

Example:

```text
Gate ID: HAG-MERGE-001
Subject: final production-like smoke for PR #42
Trigger / evidence: preview deployment for HEAD abc123
Expected observation: login, primary CRUD journey, and responsive navigation succeed
Approver: repository owner
Status: PENDING
Freshness boundary: HEAD abc123 / preview deployment <id>
Next action: when PASSED, mark PR Ready for Review or merge as appropriate
```

The agent may prepare everything else, but it must not represent the work as fully ready if this gate is required and still pending.

## Continuation Prompt interaction

Whenever work pauses for an async/human gate, produce a ready-to-paste Continuation Prompt containing:

- repository;
- base branch;
- active branch;
- PR;
- HEAD;
- active Spec Kit feature;
- all unresolved required Human Async Gates;
- automated gate state;
- one exact next action;
- a freshness instruction to re-check repository/PR/gate state before acting.

A Continuation Prompt is derived operational context, not canonical authority. Git-backed state wins if the prompt becomes stale.
