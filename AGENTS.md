# AGENTS.md

This repository uses GitHub Spec Kit for material feature development.

## Start Here

Before changing a material feature, read:

1. `.specify/memory/constitution.md`
2. the active `specs/###-slug/spec.md`
3. its `plan.md`
4. its `tasks.md`
5. relevant ADRs under `docs/adr/`

If a material feature has no active Spec Kit artifacts, create them before implementation.

## Spec Kit Commands

Codex is the default integration and uses native skills:

- `$speckit-constitution`
- `$speckit-specify`
- `$speckit-clarify`
- `$speckit-plan`
- `$speckit-tasks`
- `$speckit-analyze`
- `$speckit-implement`
- `$speckit-converge`

OpenCode is also installed and exposes the corresponding `/speckit.*` commands.

Specifications `001` through `004` are historical retrofits. New feature work starts through Spec Kit; do not use those historical files as evidence that the earlier implementation followed Spec Kit originally.

## Architecture Rules

- `apps/web` may depend on shared contracts/providers but never Prisma/database/Fastify implementation details.
- `apps/api` keeps persistence behind repository interfaces.
- `packages/contracts` contains transport/application contracts only; never export ORM-generated types.
- TanStack Router owns route/search/URL state; TanStack Query owns remote cache.
- `DataProvider` is for generic CRUD only. Domain workflows require explicit named use cases/APIs.
- Authorization UI checks are UX only. Server authorization is authoritative and deny-by-default.
- Add a package only when there is a concrete reuse/boundary need; avoid premature internal frameworks.
- Structural/cross-cutting decisions require an ADR.

## Quality Gates

Do not weaken TypeScript or CI rules to make a change pass.

Baseline commands:

```bash
pnpm typecheck
pnpm test
pnpm build
pnpm test:storybook
pnpm e2e
```

Keep `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` enabled. Critical HTTP/database journeys must remain covered against the real reference API and PostgreSQL where applicable.

## Pull Requests

A material PR should include:

- Spec path
- tasks completed
- ADRs added/changed
- tests and validation performed
- convergence status or remaining gaps

Implementation that diverges materially from the spec/plan must update those artifacts before merge.
