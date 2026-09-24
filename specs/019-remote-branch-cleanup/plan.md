# Implementation Plan: Remote Branch Cleanup V11

**Branch**: `feat/019-remote-branch-cleanup` | **Date**: 2026-09-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/019-remote-branch-cleanup/spec.md`

## Summary

Add a post-V10 authority tier that can inspect and, only under explicit operator intent, remove the exact remote feature branch associated with a completed V8 publication after finalized V9 evidence. The deletion is guarded by expected-SHA compare-and-swap semantics, never accepts arbitrary branch authority, never bypasses remote policy and remains derived from Git/Spec Kit truth.

## Technical Context

**Language/Version**: Python >=3.13

**Primary Dependencies**: Python standard library; existing Engineering Graph configuration/publication/post-publication/lifecycle modules; Git CLI; optional GitHub CLI only where existing repository metadata inspection is already used

**Storage**: Versioned derived JSON receipts under `engineering-graph/.execution/remote-cleanup/`; no canonical database state

**Testing**: `unittest` with temporary real Git repositories/remotes plus mocks only for narrow command/error seams; full Engineering Graph regression suite

**Target Platform**: Local Linux/macOS-compatible Git working environment used by the Engineering Graph toolchain

**Project Type**: Repository-local CLI/control-plane package

**Performance Goals**: One exact-ref inspection and one guarded remote mutation per finalize attempt; no repository-wide branch scan required for the critical path

**Constraints**: argv-only process execution; `shell=False`; exact publication identity; no unconditional force/delete fallback; no product-runtime or Neo4j dependency; no mutation from status

**Scale/Scope**: One repository + one publication/branch identity per operation

## Constitution Check

### I. Spec Before Implementation

PASS. Spec 019 exists before source implementation.

### II. Backend-Agnostic Frontend and Explicit Boundaries

PASS / N/A. Change remains outside application frontend/backend runtime.

### III. Server Authority and Typed Authorization

PASS / N/A for product authorization. Git remote policy remains authoritative and is never bypassed.

### IV. Strict Types, Tests, and CI Are Gates

PASS. Destructive behavior requires targeted unit/integration coverage plus full Spec Kit, Engineering Graph and Product CI convergence.

### V. Simplicity, Ownership, and Evolvability

PASS. V11 reuses V8/V9 evidence and existing CLI patterns instead of introducing a new service or database.

### VI. Git-Authoritative Engineering Graph

PASS. Git/Spec Kit remain canonical; remote-cleanup assessments/receipts are derived and Neo4j remains optional.

Post-design re-check: PASS. No planned design requires a constitution exception.

## Project Structure

### Documentation

```text
specs/019-remote-branch-cleanup/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── remote-cleanup.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code

```text
engineering-graph/
├── src/engineering_graph/
│   ├── remote_cleanup.py
│   ├── remote_cleanup_cli.py
│   ├── lifecycle.py
│   ├── lifecycle_cli.py
│   └── runner_entry.py
└── tests/
    ├── test_remote_cleanup.py
    ├── test_remote_cleanup_cli.py
    ├── test_lifecycle.py
    └── test_lifecycle_cli.py

docs/
├── adr/0027-remote-branch-cleanup-authority-boundary.md
└── architecture/REMOTE_BRANCH_CLEANUP.md
```

**Structure Decision**: Extend the existing Python Engineering Graph control-plane package. Remote mutation logic lives in a dedicated module rather than being folded into V9 or the read-only lifecycle reducer.

## Engineering Graph References

**Constrained by ADRs**: ADR-0024 (Git Publisher), ADR-0025 (Post-Publication Human Gate Boundary), ADR-0026 (Lifecycle Projection Authority Boundary), ADR-0027 (new V11 authority boundary)

**Depends on Specs/Tasks**: `SPEC-016-GIT-PUBLISHER`, `SPEC-017-POST-PUBLICATION-LIFECYCLE`, `SPEC-018-LIFECYCLE-COORDINATOR`

**Primary implementation paths**: `engineering-graph/src/engineering_graph/remote_cleanup.py`, `engineering-graph/src/engineering_graph/remote_cleanup_cli.py`, lifecycle/runner entrypoint integration files

**Primary validation paths**: `engineering-graph/tests/test_remote_cleanup.py`, `engineering-graph/tests/test_remote_cleanup_cli.py`, lifecycle regression tests, repository CI workflows

## Phase 0 Research Result

Research selects: post-V9 authority, publication-owned target identity, expected-SHA guarded deletion, read-only status, derived receipts and fail-closed local ownership checks. No unresolved clarification remains.

## Phase 1 Design

### Control flow

```text
V8 PublicationRecord
      +
V9 finalized receipt
      +
current local ownership / remote exact ref
      |
      v
RemoteCleanupAssessment (read-only)
      |
      +-- blocked / already_absent
      |
explicit operator delete intent
      |
      v
guarded exact-ref delete with expected SHA
      |
      v
RemoteCleanupReceipt (derived)
      |
      +--> lifecycle projection / continuation context
```

### Mutation boundary

Only the guarded remote-head deletion is new authority. V11 does not alter canonical Task files, PR state, local branches, worktrees, leases, tags, branch policy or Neo4j.

## Complexity Tracking

No constitution violations require justification.
