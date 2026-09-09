# Feature Specification: Observability and Audit

**Feature Branch**: `feat/006-observability-audit`

**Created**: 2026-09-09

**Status**: Draft

**Input**: Add an enterprise observability and audit baseline with request correlation, structured operational telemetry, durable append-only audit events for protected customer mutations, and clear separation between logs, security events, telemetry, and audit records.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correlate an API Interaction (Priority: P1)

As an operator investigating an API interaction, I can use one correlation identifier to connect the client-visible response with server-side operational evidence so that failures and slow requests can be diagnosed without guessing which log entries belong together.

**Why this priority**: Correlation is the minimum useful observability primitive and becomes the common context for logs, traces, errors, security events, and audit records.

**Independent Test**: Make successful and failing API requests and verify each receives a correlation identifier that matches the identifier attached to the corresponding error/security/telemetry evidence.

**Acceptance Scenarios**:

1. **Given** any API request, **When** the server handles it, **Then** it assigns a non-empty request correlation identifier and returns that identifier to the caller.
2. **Given** an API request that returns an application error, **When** the client receives the error envelope, **Then** the envelope request identifier matches the response correlation identifier.
3. **Given** a protected request that emits a security event, **When** an operator examines that event, **Then** it carries the same correlation identifier as the request.
4. **Given** operational telemetry is enabled, **When** an API request executes, **Then** the generated request telemetry can be correlated with the same request interaction without changing domain route behavior.

---

### User Story 2 - Audit Successful Customer Mutations (Priority: P1)

As an administrator or auditor, I can determine who changed a customer, what operation occurred, when it happened, what changed, and which request caused it so that administrative changes have durable accountability.

**Why this priority**: Enterprise administrative applications need durable evidence for privileged state changes that is distinct from transient logs and traces.

**Independent Test**: Perform customer create, update, and delete operations as an authorized user and verify exactly one durable audit event exists for each successful mutation with actor, action, subject, timestamps, safe before/after state, and correlation identifier.

**Acceptance Scenarios**:

1. **Given** an authorized user creates a customer, **When** the mutation commits successfully, **Then** exactly one immutable audit event records the actor, create action, customer identity, resulting safe state, occurrence time, and request correlation identifier.
2. **Given** an authorized user updates a customer, **When** the mutation commits successfully, **Then** exactly one immutable audit event records the safe before and after states for the changed customer.
3. **Given** an authorized user deletes a customer, **When** the mutation commits successfully, **Then** exactly one immutable audit event preserves the safe pre-delete state and identifies the deleted customer.
4. **Given** an authorized administrator, **When** audit history is requested, **Then** the administrator can retrieve audit events in a bounded, newest-first representation without modifying them.

---

### User Story 3 - Prevent Audit Gaps and False Audit Records (Priority: P1)

As a system owner, I can rely on the audit trail to represent committed protected mutations without gaps or phantom successes.

**Why this priority**: An audit system that can diverge from domain state gives false assurance and is worse than an explicitly unavailable audit function.

**Independent Test**: Force audit persistence to fail during a customer mutation and verify neither the domain change nor an audit event is committed; also exercise validation, forbidden, and not-found mutations and verify they do not append successful domain audit events.

**Acceptance Scenarios**:

1. **Given** audit persistence fails during an audited mutation, **When** the request executes, **Then** the domain mutation and its audit event are rolled back together and the request does not report success.
2. **Given** a mutation is forbidden before domain execution, **When** the request is denied, **Then** no successful customer audit event is appended.
3. **Given** validation or domain processing rejects a mutation, **When** no customer change is committed, **Then** no successful customer audit event is appended.
4. **Given** a committed customer mutation, **When** audit history is inspected, **Then** there is exactly one matching domain audit event rather than zero or duplicates.

---

### User Story 4 - Keep Operational Telemetry Separate from Audit (Priority: P2)

As an operator or maintainer, I can reason about logs, security events, telemetry, and audit records as separate data products with different purposes so that diagnostic noise is not mistaken for durable business evidence.

**Why this priority**: Mixing these concerns creates retention, privacy, compliance, and reliability problems as the starter grows.

**Independent Test**: Execute successful, forbidden, and failed operations and verify operational/security evidence may be emitted while durable domain audit is appended only for committed audited mutations.

**Acceptance Scenarios**:

1. **Given** a forbidden protected request, **When** it is rejected, **Then** a security/operational event may describe the denial while no successful domain audit event is created.
2. **Given** a read-only request, **When** it succeeds, **Then** operational telemetry can describe the request without creating a customer mutation audit event.
3. **Given** telemetry exporting is disabled or unavailable, **When** the application runs, **Then** domain behavior and required audit persistence continue to function independently.

### Edge Cases

- Multiple concurrent mutations of the same customer retain distinct correlation identifiers and audit records.
- Retrying a client request after an unknown network outcome must not cause an audit event to claim a mutation that was not committed; idempotency of arbitrary client retries is outside this feature unless the domain operation itself provides it.
- Audit serialization must not record passwords, session cookies, bearer tokens, authorization headers, authentication secrets, or raw provider session objects.
- An audit-history request must be bounded to prevent unbounded database reads.
- A deleted customer remains identifiable from its audit event even though the current domain row no longer exists.
- Operational telemetry/exporter failure must not silently disable mandatory audit persistence.
- Audit records are append-only in the application surface: this feature exposes no update or delete operation for audit history.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every API request MUST have a server-assigned non-empty correlation identifier.
- **FR-002**: Every API response MUST expose the request correlation identifier to the caller using a stable response contract.
- **FR-003**: Application error responses MUST include the same request identifier as the response correlation identifier.
- **FR-004**: Structured operational logs and security events emitted for a request MUST include that request correlation identifier.
- **FR-005**: The system MUST support request tracing/telemetry without requiring domain routes to depend directly on a telemetry vendor or exporter.
- **FR-006**: Telemetry exporting MUST be optional and MUST NOT be required for core domain execution or durable audit persistence.
- **FR-007**: Successful customer create, update, and delete operations MUST append exactly one durable audit event.
- **FR-008**: A customer audit event MUST identify the authenticated actor, action, subject type, subject identifier, occurrence time, and request correlation identifier.
- **FR-009**: Create audit events MUST capture an allowlisted safe resulting state; update events MUST capture allowlisted safe before and after states; delete events MUST capture an allowlisted safe pre-delete state.
- **FR-010**: Audit state snapshots MUST exclude authentication credentials, provider sessions, cookies, authorization headers, application secrets, and unrelated request payload fields.
- **FR-011**: Customer domain mutation and its required audit event MUST commit atomically as one logical transaction.
- **FR-012**: If required audit persistence fails, the associated customer mutation MUST NOT remain committed and the request MUST NOT report success.
- **FR-013**: Forbidden, unauthenticated, validation-failed, not-found, conflict, and otherwise uncommitted customer mutations MUST NOT append a successful customer mutation audit event.
- **FR-014**: Audit history MUST be append-only through the application surface; no audit update/delete operation is provided by this feature.
- **FR-015**: An authenticated user MUST require an explicit audit-read capability to retrieve audit history.
- **FR-016**: The reference authorization policy MUST grant audit-read access to Admin and deny it to Manager and Viewer.
- **FR-017**: Audit history retrieval MUST be bounded, ordered newest-first, and support continuation through a stable pagination contract.
- **FR-018**: Audit history MUST remain readable after the corresponding customer is deleted.
- **FR-019**: Operational logs, security events, telemetry, and durable audit records MUST remain separate abstractions and persistence/lifecycle concerns.
- **FR-020**: Existing authentication, authorization, data-provider, error-envelope, strict type, and CI guarantees MUST remain intact.

### Key Entities

- **Correlation Context**: Per-request operational identity used to join a response with server-side diagnostic/security/telemetry/audit evidence.
- **Audit Event**: Immutable application record describing one committed auditable domain mutation.
- **Audit Actor**: Stable authenticated Principal identity responsible for the audited action.
- **Audit Subject**: Domain object affected by an audited action, identified independently of whether its current row still exists.
- **Audit Snapshot**: Allowlisted representation of relevant domain state before and/or after a mutation.
- **Audit Action**: Stable action identifier describing the committed operation, initially customer create/update/delete.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In automated tests, 100% of API responses include a non-empty request correlation identifier.
- **SC-002**: In automated error tests, 100% of application error envelopes expose the same request identifier returned in the response correlation header.
- **SC-003**: In automated customer mutation tests, 100% of committed create/update/delete operations produce exactly one matching durable audit event.
- **SC-004**: In rollback tests where audit persistence is forced to fail, 0% of the associated customer mutations remain committed.
- **SC-005**: In forbidden, unauthenticated, validation-failed, not-found, and otherwise uncommitted mutation tests, 0 successful customer mutation audit events are appended.
- **SC-006**: Audit snapshot/security tests find zero reusable authentication secrets, session credentials, authorization headers, or unrelated raw request payloads in persisted audit state.
- **SC-007**: Admin can retrieve bounded audit history while Manager and Viewer are denied in 100% of authorization-matrix tests.
- **SC-008**: Trace/telemetry instrumentation can be enabled or disabled without changing domain route code or changing customer/audit correctness in automated tests.

## Assumptions

- Customer mutations are the reference domain used to prove the reusable audit architecture; additional resources can opt in later.
- The first audit-history surface is an API contract; a dedicated audit UI is outside this feature.
- Audit retention, archival, legal hold, export, redaction workflows, and external SIEM forwarding are separate operational/compliance decisions.
- Multi-tenancy remains inactive. Audit records may reserve an optional tenant field for future context without making tenant behavior part of this feature.
- Browser-side OpenTelemetry instrumentation is not required by this feature; server-side request telemetry is the reference baseline.
- Existing security-event logging remains diagnostic/security evidence and is not reclassified as durable domain audit.
