# Feature Specification: Opportunity Workflow

**Feature Branch**: `feat/007-opportunity-workflow`

**Created**: 2026-09-09

**Status**: Draft

**Input**: Add a reference CRM Opportunity workflow that proves CPXLabs Admin supports non-CRUD domain behavior through explicit commands, server-authoritative lifecycle rules, optimistic concurrency, typed capabilities, reusable audit, and an enterprise workflow UI without adding workflow commands to the generic DataProvider.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View a Sales Opportunity Pipeline (Priority: P1)

As an authenticated user with opportunity read access, I can list and inspect opportunities with their current stage, value, account, expected close date, and version so that I can understand pipeline state without mutating it.

**Why this priority**: Read/query behavior establishes the resource and gives every role a useful, independently testable slice before command behavior is introduced.

**Independent Test**: Sign in as Viewer, load the opportunity list and one detail view, and verify the current workflow stage and business fields are visible while mutation controls are absent.

**Acceptance Scenarios**:

1. **Given** an authenticated Viewer, Manager, or Admin, **When** opportunity history is requested, **Then** the user can retrieve a bounded opportunity list and individual detail records.
2. **Given** an opportunity, **When** its detail is shown, **Then** the current stage, version, account, amount/currency, expected close date, and last update time are visible.
3. **Given** a Viewer, **When** the opportunity UI is rendered, **Then** create and workflow-transition actions are not offered.

---

### User Story 2 - Create an Opportunity (Priority: P1)

As a Manager or Admin, I can create a new opportunity that enters the workflow in the initial Qualification stage so that opportunities always begin from a valid lifecycle state.

**Why this priority**: Creation establishes the domain aggregate and prevents callers from selecting arbitrary initial workflow state.

**Independent Test**: Create an opportunity as Manager and verify the server assigns Qualification, version 1, and the canonical persisted timestamps regardless of any client attempt to provide a different stage/version.

**Acceptance Scenarios**:

1. **Given** a Manager or Admin with valid opportunity input, **When** the opportunity is created, **Then** it starts in `qualification` with version `1`.
2. **Given** a Viewer, **When** creation is attempted directly against the API, **Then** the request is denied and no opportunity is created.
3. **Given** invalid business input, **When** creation is attempted, **Then** validation rejects it without creating an opportunity or successful audit record.

---

### User Story 3 - Advance an Opportunity Through Explicit Domain Commands (Priority: P1)

As a Manager or Admin, I can execute only valid lifecycle transitions through explicit workflow commands so that the opportunity stage cannot be changed by generic CRUD mutation.

**Why this priority**: This is the architecture gate proving the starter supports non-CRUD domain workflows and keeps business commands outside the generic DataProvider.

**Independent Test**: Starting from Qualification, execute the valid forward command sequence and verify each transition is accepted, while skipped/reversed/terminal transitions and generic stage PATCH attempts are rejected.

**Acceptance Scenarios**:

1. **Given** an opportunity in `qualification`, **When** an authorized user transitions it to `discovery`, **Then** the command succeeds and increments the version exactly once.
2. **Given** an opportunity in `discovery`, **When** a user attempts to jump directly to `negotiation`, **Then** the command is rejected without changing stage/version.
3. **Given** an opportunity in any non-terminal stage, **When** an authorized user transitions it to `lost` with a non-empty loss reason, **Then** the opportunity becomes terminal and preserves the loss reason.
4. **Given** an opportunity in `negotiation`, **When** an authorized user transitions it to `won`, **Then** the opportunity becomes terminal.
5. **Given** an opportunity in `won` or `lost`, **When** any further transition is attempted, **Then** the command is rejected and the opportunity remains unchanged.
6. **Given** an opportunity, **When** a client attempts to change `stage`, `version`, or `lossReason` through a generic update endpoint, **Then** no such generic workflow mutation surface exists.

---

### User Story 4 - Reject Stale Concurrent Workflow Commands (Priority: P1)

As a system owner, I can rely on optimistic concurrency so that two operators cannot unknowingly overwrite each other's workflow decisions.

**Why this priority**: Enterprise workflow actions are unsafe if stale clients can apply commands against state they did not observe.

**Independent Test**: Read version N, successfully transition with expectedVersion N, then retry another transition with expectedVersion N and verify a conflict response with no state/audit change.

**Acceptance Scenarios**:

1. **Given** an opportunity at version N, **When** a valid command includes `expectedVersion=N`, **Then** the transition commits and returns version N+1.
2. **Given** the same opportunity has already advanced to N+1, **When** a stale command still supplies N, **Then** it is rejected as a workflow conflict.
3. **Given** a stale/invalid command, **When** it is rejected, **Then** no workflow state or successful opportunity audit event is appended.

---

### User Story 5 - Preserve Durable Opportunity Workflow Evidence (Priority: P2)

As an Admin or auditor, I can correlate successful opportunity creation and stage changes with durable audit events so that non-CRUD commands have the same accountability guarantees as customer mutations.

**Why this priority**: The audit platform should prove it can be reused by a second resource without turning into customer-specific infrastructure.

**Independent Test**: Create and transition an opportunity, query audit history, and verify safe opportunity snapshots, actor, action, subject, request correlation, and exactly-one semantics.

**Acceptance Scenarios**:

1. **Given** a committed opportunity creation, **When** audit history is inspected, **Then** exactly one `opportunities.create` event identifies the new opportunity and safe resulting state.
2. **Given** a committed workflow transition, **When** audit history is inspected, **Then** exactly one `opportunities.stage.change` event records safe before/after workflow state and the same request correlation id.
3. **Given** a forbidden, validation-failed, invalid-transition, stale-version, or otherwise uncommitted command, **When** audit history is inspected, **Then** no successful opportunity domain audit event exists for that failed command.

### Edge Cases

- Two valid transition commands arriving concurrently with the same expected version result in at most one committed transition.
- `lost` requires a non-blank human-readable reason; other target stages must not accept a loss reason as workflow state.
- Terminal `won` and `lost` opportunities cannot transition further in this reference workflow.
- Amount must be non-negative and is represented as integer minor currency units to avoid floating-point ambiguity.
- Currency is an uppercase ISO-style three-letter code in the reference contract; broader currency validation is outside this feature.
- Expected close date is a calendar date and may be in the past for imported/reference data; no forecasting policy is imposed here.
- Workflow commands remain server authoritative even if the UI hides unavailable actions.
- A missing opportunity returns not-found rather than a workflow conflict.
- Retry/idempotency keys for ambiguous network retries are outside this feature; optimistic concurrency protects stale state but is not a general idempotency protocol.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose a reference Opportunity resource with id, name, account name, amount in minor units, currency, expected close date, stage, version, optional loss reason, created time, and updated time.
- **FR-002**: Opportunity stage MUST use exactly `qualification`, `discovery`, `proposal`, `negotiation`, `won`, or `lost` in the reference workflow.
- **FR-003**: Opportunity creation MUST assign `qualification` and version `1` server-side; clients MUST NOT choose initial stage/version.
- **FR-004**: The reference workflow MUST allow `qualification → discovery`, `discovery → proposal`, `proposal → negotiation`, and `negotiation → won` as forward transitions.
- **FR-005**: Any non-terminal stage MUST allow transition to `lost` only when a non-blank loss reason is supplied.
- **FR-006**: `won` and `lost` MUST be terminal states in this feature.
- **FR-007**: Skipped, reversed, terminal, or otherwise invalid transitions MUST be rejected without changing persisted workflow state.
- **FR-008**: Workflow stage changes MUST be executed through an explicit domain command surface rather than generic CRUD update semantics or the generic frontend DataProvider.
- **FR-009**: Every workflow command MUST include the version observed by the caller as `expectedVersion`.
- **FR-010**: A command whose expected version differs from current persisted version MUST be rejected as a conflict without changing workflow state.
- **FR-011**: Every committed stage transition MUST increment the opportunity version exactly once.
- **FR-012**: The server MUST remain authoritative for opportunity workflow validation regardless of frontend capability/action visibility.
- **FR-013**: The system MUST add typed `opportunities.read`, `opportunities.create`, and `opportunities.transition` capabilities.
- **FR-014**: Admin and Manager MUST receive all three opportunity capabilities; Viewer MUST receive only `opportunities.read`.
- **FR-015**: Opportunity list/detail MUST require `opportunities.read`; creation MUST require `opportunities.create`; workflow commands MUST require `opportunities.transition`.
- **FR-016**: The Opportunity resource registry entry MUST expose list/detail/create discoverability without inventing a generic edit/delete route for workflow state.
- **FR-017**: Successful opportunity creation and stage commands MUST append durable audit evidence using the existing audit architecture with `opportunity` subject type.
- **FR-018**: Opportunity audit snapshots MUST be explicit allowlists and MUST NOT include authentication/session/secrets or arbitrary raw request data.
- **FR-019**: Opportunity domain state and its required audit event MUST commit atomically for audited create/transition commands.
- **FR-020**: Forbidden, invalid, stale, not-found, or otherwise uncommitted opportunity commands MUST NOT append successful opportunity audit events.
- **FR-021**: The web application MUST use a domain-specific opportunity workflow service/client for command execution rather than adding opportunity transition methods to the generic DataProvider contract.
- **FR-022**: The web detail experience MUST present only currently valid next workflow actions allowed by lifecycle state and capability, while treating the API as authoritative.
- **FR-023**: After a successful command, the web application MUST refresh/invalidate affected opportunity list/detail server state so the displayed stage/version is authoritative.
- **FR-024**: Stale workflow conflicts MUST produce a stable application error the web client can distinguish from validation/not-found/forbidden failures and recover from by refreshing current state.
- **FR-025**: Existing authentication, authorization, customer CRUD, audit, telemetry, strict TypeScript, accessibility, and CI guarantees MUST remain intact.

### Key Entities

- **Opportunity**: CRM aggregate whose lifecycle is controlled by explicit workflow commands.
- **Opportunity Stage**: Finite lifecycle state with a constrained transition graph.
- **Opportunity Transition Command**: Authorized request to move one opportunity from its observed state/version to a valid target stage.
- **Opportunity Version**: Monotonically increasing integer used for optimistic concurrency.
- **Loss Reason**: Required business explanation when the target terminal stage is `lost`.
- **Opportunity Audit Snapshot**: Allowlisted opportunity state used in durable audit evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Automated lifecycle tests accept 100% of the documented valid transitions and reject 100% of documented invalid/skipped/terminal transitions.
- **SC-002**: Automated concurrency tests demonstrate that two commands using the same expected version result in at most one committed transition.
- **SC-003**: 100% of committed opportunity creates/transitions increment or initialize version exactly as specified.
- **SC-004**: 100% of forbidden, invalid-transition, stale-version, not-found, and validation-failed commands append zero successful opportunity audit events.
- **SC-005**: 100% of committed opportunity create/transition operations append exactly one matching durable audit event with safe snapshots and request correlation.
- **SC-006**: Authorization-matrix tests show Admin/Manager can create/transition and Viewer can only read in 100% of tested cases.
- **SC-007**: Frontend architecture tests/code boundaries show no opportunity workflow command added to the generic DataProvider interface.
- **SC-008**: Browser tests prove Viewer sees read-only opportunity state while Manager/Admin can execute valid workflow actions and stale conflict recovery refreshes authoritative state.
- **SC-009**: Existing quality, browser, and Spec Kit CI gates remain green after the feature is integrated.

## Assumptions

- This is a reference CRM workflow intended to prove reusable architecture rather than encode every organization's sales process.
- Backward stage transitions, reopening terminal opportunities, custom pipelines, per-tenant workflow configuration, approval gates, and probability forecasting are future extensions.
- Opportunity deletion is intentionally outside this feature; terminal state is represented through `won`/`lost`, not row deletion.
- Opportunity ownership/assignment to sales representatives is outside the first reference workflow and can be layered later.
- A dedicated pipeline Kanban visualization is optional polish; the required UI is a clear list/detail/create/workflow-action experience.
