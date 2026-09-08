# Contract: Application Session and Authorization

## Purpose

Define the application-owned contract between the Vite web app and Fastify API. Provider-specific Better Auth endpoints remain an implementation detail behind the web `AuthService` and API authentication adapter.

## GET `/api/session`

Returns the current application Principal derived from the authenticated identity session and current application access profile.

### Success — `200 OK`

```json
{
  "principal": {
    "id": "user-id",
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin",
    "capabilities": [
      "customers.read",
      "customers.create",
      "customers.edit",
      "customers.delete"
    ]
  }
}
```

Rules:

- `capabilities` contains application capabilities only.
- No password, credential hash, account token, session token, or provider-internal authorization state is returned.
- Role and capabilities reflect the current application access profile at request time.

### No valid identity session — `401 Unauthorized`

Uses the existing API error envelope:

```json
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication is required",
    "requestId": "request-id"
  }
}
```

### Valid identity but no active application access — `403 Forbidden`

```json
{
  "error": {
    "code": "ACCESS_DISABLED",
    "message": "Application access is not available",
    "requestId": "request-id"
  }
}
```

The response must not reveal role/capability details for disabled or missing access profiles.

## Provider Authentication Endpoints

The web `AuthService` may call provider endpoints mounted below `/api/auth/*`, including the reference email/password sign-in and sign-out operations. Feature and domain code MUST NOT call provider endpoints directly.

Expected reference operations:

- sign in with email/password
- sign out current session
- provider session validation used by the API adapter

The exact provider request/response schema is not promoted into `packages/contracts`; it remains isolated behind the authentication adapter.

## Protected Domain API Semantics

### Unauthenticated

Every protected domain endpoint returns `401` with code `AUTHENTICATION_REQUIRED` when no valid application Principal can be resolved from the identity session.

### Authenticated but forbidden

Every protected domain endpoint returns `403` with code `FORBIDDEN` when the Principal does not contain the capability required by the operation.

### Customer capability mapping

| Operation | Required capability |
|---|---|
| list/get customer | `customers.read` |
| create customer | `customers.create` |
| update customer | `customers.edit` |
| delete customer | `customers.delete` |

Authorization is evaluated before repository mutation or protected record serialization.

## Web Authentication Boundary

The web application exposes an app-owned interface conceptually equivalent to:

```text
AuthService
- signIn(email, password): Promise<void>
- signOut(): Promise<void>
- getSession(): Promise<SessionResponse | null>
```

Components and domain features depend on this boundary or on `AuthorizationProvider`, not on Better Auth client types.

## Routing Behavior

- `/sign-in` is public.
- Protected application routes require an authenticated application Principal.
- Navigating unauthenticated to a protected route redirects to `/sign-in` with a safe return target.
- Successful sign-in returns to the intended protected target when valid; otherwise it uses the application default protected route.
- Authenticated navigation to `/sign-in` redirects to the application default protected route.

## Security Invariants

- Session cookie is server-managed and not copied into browser storage.
- API authorization never trusts role/capability values supplied by the client.
- Missing access profile fails closed.
- Disabled access profile fails closed.
- Authentication and authorization errors use distinct 401/403 semantics.
