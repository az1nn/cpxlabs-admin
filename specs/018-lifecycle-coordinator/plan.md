# Implementation Plan: Lifecycle Coordinator V10

## Scope

Add one read-only lifecycle assessment layer over the existing V3–V9 local evidence and Human Async Gate declarations. Expose it as `lifecycle-status` through `graph-engineering` and provide structured continuation context without mutating any underlying authority tier.

## Architecture

1. Introduce a pure lifecycle reducer with a versioned assessment schema.
2. Normalize evidence from existing V3–V9 artifacts into one immutable input snapshot.
3. Validate repository/Spec/Task/branch/worktree/run/publication identity across available evidence.
4. Validate supplied Human Async Gate schema/status/freshness without mutating it.
5. Select the furthest phase actually proven.
6. If identities/evidence conflict, return `blocked` with stable blocker codes.
7. Select exactly one next action from a closed action vocabulary.
8. Generate a derived continuation payload from the assessment.
9. Add a read-only CLI command with JSON and concise human rendering.
10. Route the command through `runner_entry.py` without changing existing V1–V9 commands.

## Authority rule

The coordinator owns only interpretation/projection. It gets no mutation callback and no API for advancing another subsystem. Existing subsystem CLIs remain the only explicit path to authority-bearing operations.

## Proposed modules

- `engineering-graph/src/engineering_graph/lifecycle.py`
- `engineering-graph/src/engineering_graph/lifecycle_cli.py`
- update `engineering-graph/src/engineering_graph/runner_entry.py`

## Evidence adapter strategy

Keep the reducer independent of filesystem/process/GitHub mutation. CLI/adapters may read existing registries and receipts, then convert them into a small immutable `LifecycleEvidence` structure. This keeps classification testable and prevents status computation from accidentally performing side effects.

The first version may accept an explicit JSON evidence file for Human Async Gates because those gates are not a canonical runtime registry. That evidence remains external/derived and freshness-bound.

## Tests

- schema/roundtrip and closed vocabulary;
- each lifecycle phase transition without skipping tiers;
- missing evidence selects the correct next action;
- identity conflict fails closed;
- runner success does not imply validation;
- validation does not imply publication;
- publication does not imply merge/canonical completion;
- required pending/failed/stale Human Async Gates block appropriately;
- continuation payload contains required fields and freshness instruction;
- CLI JSON/human output;
- read-only/no-write behavior;
- full V1–V9 Engineering Graph regression suite.

## Documentation

- ADR-0026: lifecycle projection authority boundary;
- V10 architecture/operator documentation;
- Engineering Graph agent instructions and README command index;
- Spec analysis/convergence evidence.

## Freeze

Final readiness requires Spec Kit + Engineering Graph + Product CI green on the exact same final HEAD and no required Human Async Gate remaining `PENDING`. Any content commit after a candidate freeze invalidates it and requires all three gates again.