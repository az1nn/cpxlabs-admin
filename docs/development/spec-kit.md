# Spec Kit Development Workflow

`cpxlabs-admin` uses GitHub Spec Kit as the required workflow for material feature development.

## Pinned Baseline

The repository was initialized with Spec Kit `v1.0.4`. Codex is the versioned default integration and its native skills live under `.agents/skills/`.

OpenCode remains supported, but it is not versioned as a simultaneous integration because Spec Kit v1.0.4 reports the OpenCode + Codex combination as unsafe for multi-install. Use the official integration switch when working with OpenCode rather than keeping both managed layouts committed at once.

Do not hand-edit generated Spec Kit command/skill files. Upgrade or switch them through the Specify CLI.

## Workflow

For a new feature:

```text
constitution
    ↓
specify
    ↓
clarify (when needed)
    ↓
plan
    ↓
tasks
    ↓
analyze/checklist (when useful)
    ↓
implement
    ↓
converge
```

Repeat implementation/convergence until the feature is converged or remaining gaps are explicitly documented.

### Codex (repository default)

Codex uses skills installed in `.agents/skills`:

```text
$speckit-specify
$speckit-clarify
$speckit-plan
$speckit-tasks
$speckit-analyze
$speckit-implement
$speckit-converge
```

### OpenCode (local switch)

To use OpenCode for a working session:

```bash
specify integration switch opencode
```

OpenCode then exposes the `/speckit.*` command layout. Before committing managed integration files, restore the repository default:

```bash
specify integration switch codex
specify integration status
```

The feature artifacts under `specs/` are shared regardless of which supported agent executes the workflow.

## Feature Directory

Every material new feature gets a numbered directory:

```text
specs/005-example-feature/
├── spec.md
├── plan.md
├── research.md        # when produced/needed
├── data-model.md      # when produced/needed
├── quickstart.md      # when produced/needed
├── contracts/         # when produced/needed
└── tasks.md
```

`spec.md` defines what and why. `plan.md` defines the technical approach and constitution checks. `tasks.md` is the executable implementation breakdown.

## Historical Retrofit

Specifications `001` through `004` were created when Spec Kit was adopted on 2026-09-08. They document already-implemented and already-reviewed behavior so future agents have coherent historical context. They are intentionally labeled `Implemented (Retrofitted)` and are not evidence that the original work followed Spec Kit.

The first feature after adoption must be created natively through Spec Kit rather than manually copying a historical template.

## Updating Spec Kit

Check status before changing generated infrastructure:

```bash
specify integration status
specify integration list
specify self check
```

When deliberately upgrading the CLI, pin/review the target release and refresh integrations through the CLI rather than editing generated skills/commands by hand.

## Relationship to ADRs

Feature specs own scope and acceptance criteria. ADRs own durable cross-cutting decisions. A plan should reference existing ADRs and add a new ADR when the implementation changes a structural architectural rule.

## CI

Spec Kit does not replace repository gates. A feature is not complete merely because its tasks are checked. The normal CI gates remain authoritative:

- frozen dependency install
- TypeScript strict
- unit/integration/API tests
- production build
- Storybook/browser accessibility coverage
- Playwright critical journeys
- PostgreSQL integration when persistence is involved

A dedicated `Spec Kit` workflow validates the pinned CLI integration state and the required artifact shape when Spec Kit/spec files change.
