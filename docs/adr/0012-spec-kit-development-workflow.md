# ADR-0012: Adopt GitHub Spec Kit for Feature Development

- **Status:** Accepted
- **Date:** 2026-09-08

## Context

The repository was developed with architecture-first documentation, ADRs, CI gates, and iterative reviews, but the implementation lifecycle was not actually managed by GitHub Spec Kit. This created a gap between the intended spec-driven process and the repository artifacts available to coding agents.

The project is intended to support agent-driven implementation with Codex and OpenCode while preserving architecture constraints over time.

## Decision

Adopt GitHub Spec Kit `v1.0.4` as the feature-development workflow.

- Codex is the versioned default Spec Kit integration using native skills under `.agents/skills/`.
- OpenCode remains a supported execution environment, but it is used through `specify integration switch opencode` rather than committed simultaneously. Spec Kit v1.0.4 reports OpenCode as unsafe for multi-install alongside Codex.
- `.specify/` is generated and managed through the official Specify CLI.
- The repository constitution lives at `.specify/memory/constitution.md`.
- Material future features must use the Spec Kit lifecycle: specification, plan, tasks, implementation, and convergence.
- Existing work is backfilled into `specs/001` through `specs/004` and explicitly marked as historical retrofit.
- ADRs remain the record for durable cross-cutting architecture decisions and complement rather than replace feature specs.

## Consequences

### Positive

- Agents receive explicit project governance and feature scope before implementation.
- Requirements, implementation plans, tasks, and convergence become traceable.
- Codex and OpenCode can execute against the same feature artifacts while the repository maintains one safe managed integration state.
- Architectural decisions remain connected to implementation work instead of existing only as background documentation.

### Trade-offs

- Material features require more artifact discipline before coding.
- Generated Spec Kit files must be upgraded/switched through the Specify CLI rather than casually edited.
- Switching to OpenCode locally changes managed integration files; the repository should be restored to Codex before those files are committed.
- Historical specs contain retrospective documentation and therefore must be distinguished from native Spec Kit execution history.

## Alternatives Considered

### Simultaneously install Codex and OpenCode

Rejected after `specify integration status --json` reported `unsafe-multi-install` for OpenCode under Spec Kit v1.0.4. The project will not suppress or bypass that upstream safety signal.

### Continue with ADRs and free-form implementation specs only

Rejected because it does not provide a standardized executable lifecycle for coding agents or convergence against feature requirements.

### Build a custom spec workflow

Rejected because the project should avoid creating an internal framework where a maintained ecosystem tool already supplies the required workflow.

## Validation

The adoption bootstrap used the official Specify CLI pinned to `v1.0.4`. Codex was initialized through the CLI. A temporary OpenCode install was used to validate compatibility, then removed through the official CLI after the integration status gate identified unsafe simultaneous installation. The dedicated Spec Kit CI gate validates integration state and historical artifact shape, while the existing TypeScript/test/build/browser/database gates remain unchanged.
