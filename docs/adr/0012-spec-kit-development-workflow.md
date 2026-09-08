# ADR-0012: Adopt GitHub Spec Kit for Feature Development

- **Status:** Accepted
- **Date:** 2026-09-08

## Context

The repository was developed with architecture-first documentation, ADRs, CI gates, and iterative reviews, but the implementation lifecycle was not actually managed by GitHub Spec Kit. This created a gap between the intended spec-driven process and the repository artifacts available to coding agents.

The project is explicitly intended to support agent-driven implementation with Codex and OpenCode while preserving architecture constraints over time.

## Decision

Adopt GitHub Spec Kit `v1.0.4` as the feature-development workflow.

- Codex is the default Spec Kit integration using native skills under `.agents/skills/`.
- OpenCode is installed as a secondary integration using `.opencode/commands/`.
- `.specify/` is generated and managed through the official Specify CLI.
- The repository constitution lives at `.specify/memory/constitution.md`.
- Material future features must use the Spec Kit lifecycle: specification, plan, tasks, implementation, and convergence.
- Existing work is backfilled into `specs/001` through `specs/004` and explicitly marked as historical retrofit.
- ADRs remain the record for durable cross-cutting architecture decisions and complement rather than replace feature specs.

## Consequences

### Positive

- Agents receive explicit project governance and feature scope before implementation.
- Requirements, implementation plans, tasks, and convergence become traceable.
- Codex and OpenCode can work from the same feature artifacts without separate process conventions.
- Architectural decisions remain connected to implementation work instead of existing only as background documentation.

### Trade-offs

- Material features require more artifact discipline before coding.
- Generated Spec Kit files must be upgraded through the Specify CLI rather than casually edited.
- Historical specs contain retrospective documentation and therefore must be distinguished from native Spec Kit execution history.

## Alternatives Considered

### Continue with ADRs and free-form implementation specs only

Rejected because it does not provide a standardized executable lifecycle for coding agents or convergence against feature requirements.

### Build a custom spec workflow

Rejected because the project should avoid creating an internal framework where a maintained ecosystem tool already supplies the required workflow.

## Validation

The adoption bootstrap uses the official Specify CLI pinned to `v1.0.4`, initializes Codex, installs OpenCode as an additional integration, and preserves the existing TypeScript/test/build CI gates.
