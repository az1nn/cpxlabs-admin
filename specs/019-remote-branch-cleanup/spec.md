# Feature Specification: Remote Branch Cleanup V11

**Feature Branch**: `feat/019-remote-branch-cleanup`

**Created**: 2026-09-18

**Status**: Draft

**Input**: Continue the post-publication control plane after V10 by adding a narrowly scoped, explicit and fail-closed capability to remove the exact remote feature branch only after the merged work is proven complete and local execution authority is closed.

## User Scenarios & Testing

### User Story 1 - Assess remote cleanup readiness (Priority: P1)

As an operator, I can inspect whether one published branch is safe to remove from the remote without deleting anything, so I know exactly which prerequisite is missing before any destructive action.

**Why this priority**: Remote deletion must never be the discovery mechanism. A read-only readiness view is the safety boundary for every later mutation.

**Independent Test**: Given publication and V9 evidence, the status command can be exercised across ready, stale, mismatched, protected-by-policy, already-absent and unsafe-local-state scenarios while proving that no remote reference changes.

**Acceptance Scenarios**:

1. **Given** a finalized V9 receipt, no active matching lease, safe local state and a remote branch that still points at the exact V8 publication commit, **When** cleanup status is requested, **Then** the system reports the branch as deletable and identifies the exact expected remote SHA.
2. **Given** the remote branch points at a different SHA than the V8 publication commit, **When** cleanup status is requested, **Then** the system reports a blocker and never normalizes the mismatch away.
3. **Given** the target branch equals the repository base/default branch, **When** cleanup status is requested, **Then** the system reports a hard blocker.
4. **Given** the target remote branch is already absent, **When** cleanup status is requested, **Then** the system reports an idempotent already-absent state rather than an error requiring mutation.

---

### User Story 2 - Delete only the proven remote branch (Priority: P2)

As an operator, I can explicitly delete the one remote branch proven safe by current evidence, with compare-and-swap semantics that fail if the remote reference changed after inspection.

**Why this priority**: The value of V11 is safe cleanup, but mutation is permitted only after the read-only contract is complete.

**Independent Test**: A controlled Git remote can prove that the exact expected branch is deleted, while a changed SHA, wrong repository, wrong branch, default branch, active lease or unsafe local state prevents deletion and leaves every remote reference untouched.

**Acceptance Scenarios**:

1. **Given** all cleanup prerequisites remain current, **When** the operator explicitly requests remote deletion, **Then** the exact target branch is deleted only if it still points at the expected publication SHA.
2. **Given** the target branch changes between readiness inspection and deletion, **When** deletion is attempted, **Then** compare-and-swap protection rejects the mutation and the branch remains present.
3. **Given** a sibling branch or unrelated reference exists, **When** deletion succeeds, **Then** those references are unchanged.
4. **Given** no explicit deletion intent is supplied, **When** the finalize command is invoked, **Then** no remote mutation occurs.

---

### User Story 3 - Preserve lifecycle and continuation evidence (Priority: P3)

As an operator or continuation agent, I can see whether remote cleanup is pending, blocked, completed or already unnecessary, with enough identity and freshness evidence to resume safely in a later session.

**Why this priority**: Cleanup must remain reconstructable and idempotent across chats, crashes and retries.

**Independent Test**: A completed or blocked cleanup can be reloaded from derived evidence and reflected by lifecycle status without turning the receipt into canonical Task truth or duplicating deletion.

**Acceptance Scenarios**:

1. **Given** remote deletion completed, **When** status is requested again, **Then** the result is stable and does not issue another destructive command.
2. **Given** deletion is blocked by changed remote identity, **When** a continuation payload is produced, **Then** it names the blocker, expected SHA, observed SHA and one safe next action.
3. **Given** V11 evidence exists, **When** lifecycle status is computed, **Then** the coordinator may expose remote-cleanup readiness/completion without changing canonical Spec Kit state or Neo4j truth.

### Edge Cases

- The remote branch disappeared outside V11 after V9 finalization.
- The remote branch was recreated after a prior successful cleanup.
- The branch name contains characters that are valid in Git refs but unsafe to interpolate into shell text.
- The configured remote is missing or cannot be reached.
- The remote reports multiple or malformed matches for the exact requested branch.
- The publication record is terminal but lacks the commit SHA needed for compare-and-swap deletion.
- A matching worktree or active lease still exists locally.
- The branch equals the configured base branch or repository default branch.
- Remote deletion is denied by server-side branch/ruleset policy.
- A prior derived cleanup receipt conflicts with current remote state.

## Requirements

### Functional Requirements

- **FR-001**: V11 MUST provide a read-only remote-cleanup assessment for exactly one V8 publication / V9 lifecycle identity.
- **FR-002**: The assessment MUST require a terminal V8 publication with an exact publication commit SHA and a matching finalized V9 receipt.
- **FR-003**: Repository, Spec, Task, publication, PR, branch and base identities MUST match across V8/V9 evidence.
- **FR-004**: The target branch MUST be the exact publication branch; arbitrary branch names supplied only by an operator MUST NOT become deletion authority.
- **FR-005**: The target branch MUST NOT equal the configured base branch or the repository default branch.
- **FR-006**: V11 MUST verify that no matching active lease remains before declaring remote deletion ready.
- **FR-007**: V11 MUST fail closed when a matching registered worktree or equivalent local execution ownership makes remote deletion unsafe; V11 MUST NOT remove that worktree itself.
- **FR-008**: V11 MUST inspect the exact remote branch ref without using shell interpolation.
- **FR-009**: A present target branch MUST point at the exact V8 publication commit SHA before deletion can be declared ready.
- **FR-010**: A mismatched remote SHA MUST be surfaced as a blocker with expected and observed identities.
- **FR-011**: An already-absent target branch MUST be represented as an idempotent terminal outcome and MUST NOT trigger a destructive retry.
- **FR-012**: Remote deletion MUST require explicit operator intent distinct from read-only status.
- **FR-013**: Deletion MUST use compare-and-swap / expected-SHA protection so a remote branch change between inspection and mutation fails closed.
- **FR-014**: V11 MUST NOT force deletion without expected-SHA protection and MUST NOT fall back to an unconditional delete when the guarded delete fails.
- **FR-015**: V11 MUST NOT delete local branches, tags, sibling refs, worktrees, leases, PRs or any branch other than the exact target remote head.
- **FR-016**: V11 MUST NOT change branch protection/rulesets or bypass remote policy.
- **FR-017**: V11 MUST persist a versioned derived cleanup receipt sufficient for idempotent recovery and audit.
- **FR-018**: The receipt MUST record repository, publication, Task, Spec, branch, remote, expected SHA, observed SHA, outcome, timestamps and blocker/error evidence when applicable.
- **FR-019**: Re-running cleanup after a successful deletion MUST NOT issue a duplicate delete.
- **FR-020**: Re-running cleanup after an external already-absent state MUST remain non-destructive.
- **FR-021**: V11 MUST expose JSON and concise human-readable status through the standard `graph-engineering` entrypoint.
- **FR-022**: The read-only status operation MUST not write Git refs, remote refs, `.execution/`, Neo4j or product runtime state.
- **FR-023**: The mutation path MUST use argv execution with `shell=False` or equivalent non-shell process semantics.
- **FR-024**: V11 MUST preserve Git/Spec Kit as canonical Task truth; cleanup receipts remain derived evidence.
- **FR-025**: V11 MUST remain outside product runtime and MUST NOT make Neo4j required for cleanup decisions.
- **FR-026**: Lifecycle Coordinator output MAY be extended to distinguish pending/blocked/completed remote cleanup, but that projection MUST remain derived and read-only.
- **FR-027**: Any lifecycle contract version change MUST preserve explicit migration/backward-compatibility semantics for existing V10 consumers.
- **FR-028**: Failure of remote policy, network access or guarded deletion MUST produce a blocker/error without claiming cleanup success.
- **FR-029**: Tests MUST prove exact-ref targeting, no-shell execution, expected-SHA race protection, idempotency and preservation of unrelated refs.
- **FR-030**: Final convergence MUST require Spec Kit, Engineering Graph and Product CI green on the same final HEAD plus no required Human Async Gate left PENDING.

### Key Entities

- **RemoteCleanupAssessment**: Read-only decision describing target identity, expected/observed remote state, blockers and whether explicit deletion is currently allowed.
- **RemoteCleanupReceipt**: Derived, versioned evidence of a completed, already-absent or blocked cleanup attempt.
- **RemoteBranchIdentity**: Repository/remote/branch tuple plus the exact publication commit SHA used as deletion expectation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In automated race tests, 100% of remote-SHA changes between inspection and deletion are rejected without deleting the changed branch.
- **SC-002**: In automated isolation tests, successful cleanup changes exactly one intended remote head and leaves all sibling heads/tags unchanged.
- **SC-003**: Read-only status produces zero filesystem, local-ref, remote-ref and Neo4j mutations in regression tests.
- **SC-004**: Repeating status/finalize after a completed or already-absent outcome performs zero additional destructive remote operations.
- **SC-005**: Every blocked assessment identifies a concrete blocker and exactly one safe next action.
- **SC-006**: Base/default branch deletion is rejected in 100% of covered scenarios before any push/delete command is issued.
- **SC-007**: Full V1–V10 Engineering Graph regression coverage remains green with the V11 tests.
- **SC-008**: Spec Kit, Engineering Graph and Product CI all succeed on the same freeze HEAD before the feature is declared converged.

## Assumptions

- V8 publication evidence remains the authority for the exact feature branch and publication commit identity.
- V9 finalization remains the prerequisite authority boundary proving merge/canonical completion and lease cleanup; V11 does not replace it.
- The configured Git remote is `origin` unless repository configuration explicitly establishes another supported remote.
- Server-side protected-branch/ruleset policy remains authoritative and may reject deletion; V11 does not bypass it.
- Remote branch cleanup is repository hygiene, not canonical Task completion.
- No separate Human Async Gate is expected for the implementation itself unless later design introduces a manual/external acceptance condition that automated tests cannot prove.

## Out of Scope

- deleting local branches;
- deleting tags;
- deleting arbitrary operator-selected branches;
- removing worktrees or releasing leases;
- approving, merging, closing or modifying pull requests;
- changing branch protection/rulesets;
- force deletion without expected-SHA compare-and-swap protection;
- deleting branches in another repository/remote;
- deployment/release automation;
- rewriting V8/V9 receipts;
- making remote cleanup evidence canonical Task truth.
