# ADR-005: Typed Capabilities for Authorization

- Status: Accepted
- Date: 2026-09-08

## Context

Enterprise applications need authorization that scales beyond route-level role checks. Components should reason in terms of actions, while backend systems remain authoritative.

## Decision

Expose typed capabilities using a stable `<resource>.<action>` naming convention and a frontend API such as `can(capability)`.

Examples:

```text
customers.read
customers.create
customers.update
customers.delete
users.read
users.manage
```

Roles may grant capabilities, but feature code should not normally branch directly on role names.

Client-side authorization is UX only. The backend/API must re-check every privileged operation and default to deny.

## Consequences

- UI logic remains stable as role models evolve;
- RBAC can later grow toward ownership/attribute-aware rules;
- resource metadata can declare required capabilities;
- authorization vendors/policy engines remain replaceable;
- tests can target business capabilities instead of hard-coded role names.
