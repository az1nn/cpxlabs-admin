# Data Model: Clerk Authentication Provider Migration

## External identity model

Clerk owns identity and session persistence. The application does not mirror Clerk session/account/token records in PostgreSQL.

### Clerk Identity

Application-relevant fields at the adapter boundary:

- `id: string` — stable Clerk user ID; canonical foreign identity key.
- `email: string` — selected verified/primary email for display/audit.
- `name: string` — provider display name/fallback.
- authentication status — proven from a valid Clerk session token.

Provider objects must be normalized before leaving the authentication adapter.

## Application-owned model

### AccessProfile

```text
AccessProfile
- id: string (application PK)
- userId: string (unique external Clerk user ID)
- role: admin | manager | viewer
- status: active | disabled
- createdAt
- updatedAt
```

Invariants:

- `userId` is unique.
- No Prisma relation to a local `User` provider table.
- Missing profile fails closed.
- Disabled profile fails closed.
- Role is application-owned and maps to project capabilities.

### Principal

Unchanged semantic contract:

```text
Principal
- id
- email
- name
- role
- capabilities
```

Construction:

```text
valid Clerk session
    -> normalized AuthenticatedIdentity
    + current AccessProfile
    -> createPrincipal(...)
```

### RequestContext

Unchanged:

```text
RequestContext
- principal
- tenant? (future/current feature boundary)
```

## Removed provider-owned local models

The migration removes Better Auth-only models from the reference schema:

- `User`
- `Session`
- `Account`
- `Verification`

These are not replaced with Clerk tables. Clerk remains external.

## Migration ordering

1. Drop AccessProfile foreign key to Better Auth `User`.
2. Preserve `access_profiles` rows and `user_id` strings.
3. Drop Better Auth provider tables.
4. Verify domain/audit/access-profile data remains intact.
5. Provision/map Clerk IDs before production traffic cutover.

Because Better Auth user IDs and Clerk user IDs are different namespaces, existing non-demo access-profile rows cannot be assumed to map automatically. Production migration requires explicit identity mapping/provisioning and is covered by the live Human Async Gate.
