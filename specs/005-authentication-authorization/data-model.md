# Data Model: Authentication and Authorization

## Identity User

Owned by the authentication provider and persisted in PostgreSQL.

Fields relevant to application integration:

- `id`: stable string identifier; primary identity key used by application authorization.
- `name`: display name.
- `email`: unique sign-in identifier.
- `emailVerified`: provider-managed verification state.
- `createdAt` / `updatedAt`: provider-managed timestamps.

The application MUST NOT use provider-generated ORM types outside `apps/api`.

## Identity Account

Provider-owned authentication account record.

For the first slice the reference account is credential-based. Password/hash fields remain provider internals and are never returned through application contracts.

## Identity Session

Provider-owned authenticated session record.

Relevant properties:

- stable session identifier/token (secret; never returned through app contracts)
- `userId`
- `expiresAt`
- optional provider-captured IP/user-agent metadata

State transitions:

```text
created -> active -> expired
                 -> revoked
```

Revoked/expired sessions cannot resolve an application Principal.

## Application Access Profile

Application-owned authorization record, separate from the identity provider.

Proposed fields:

| Field | Type | Rules |
|---|---|---|
| `id` | string | primary key |
| `userId` | string | unique; references Identity User id |
| `role` | `admin | manager | viewer` | required |
| `status` | `active | disabled` | required; default active |
| `createdAt` | timestamp | required |
| `updatedAt` | timestamp | required |

Relationships:

```text
Identity User 1 ─── 0..1 Application Access Profile
```

If a valid identity user has no access profile, the system fails closed and produces no application Principal.

State transitions:

```text
active <-> disabled
```

A transition to `disabled` takes effect on the next protected server request even if the provider identity session itself is still active.

## Role

Roles are persisted as an enum-like value on `Application Access Profile`; capabilities are derived in code and are not stored individually.

### Admin

- `customers.read`
- `customers.create`
- `customers.edit`
- `customers.delete`

### Manager

- `customers.read`
- `customers.create`
- `customers.edit`

### Viewer

- `customers.read`

## Capability

Existing application type: `` `${string}.${string}` ``.

Capabilities are stable application permissions. A role maps to an immutable capability set in project-owned authorization code.

Future resources add capabilities to the same application-owned policy without changing authentication-provider schema.

## Principal

Canonical in-memory application identity after identity and access checks succeed.

Proposed shape:

```text
Principal
- id: string
- email: string
- name: string
- role: ApplicationRole
- capabilities: ReadonlySet<Capability>
```

A Principal exists only when:

1. the provider session is valid;
2. the identity user exists;
3. an application access profile exists;
4. that profile status is active.

## Session Principal DTO

Transport-safe representation returned by the application-owned session endpoint.

```text
SessionPrincipalDto
- id: string
- email: string
- name: string
- role: ApplicationRole
- capabilities: readonly Capability[]
```

Capabilities are serialized as an array and reconstructed into the in-memory Principal representation by the web authentication boundary.

No provider session token or password/account secret appears in this DTO.

## RequestContext

Canonical per-request server identity context.

```text
RequestContext
- principal: Principal
- tenant?: future extension only; not populated by feature 005
```

Protected application services/routes receive or resolve RequestContext rather than reading provider cookies directly.
