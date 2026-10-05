# Contract: Clerk-backed Application Session

## Boundary

Clerk's provider APIs/components remain implementation details. Browser/domain code consumes the application-owned session/authorization contract.

## Protected request credential

Protected application API calls MUST include:

```http
Authorization: Bearer <Clerk session token>
```

Rules:

- the token is obtained from Clerk's session API at request time;
- application code does not persist the token in localStorage/sessionStorage;
- cookie-only authentication is insufficient for protected application API authority;
- missing/malformed/invalid/expired/revoked token maps to `401 AUTHENTICATION_REQUIRED`;
- token contents are never logged.

## GET `/api/session`

Returns the current application Principal after:

1. Clerk session validation;
2. normalized identity resolution;
3. current application `AccessProfile` lookup;
4. current role-to-capability derivation.

### Success — 200

```json
{
  "principal": {
    "id": "user_...",
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin",
    "capabilities": [
      "customers.read",
      "customers.create",
      "customers.update",
      "customers.delete"
    ]
  }
}
```

No Clerk secret, JWT, refresh material, provider metadata, or password is returned.

### Missing/invalid Clerk identity — 401

```json
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication is required",
    "requestId": "request-id"
  }
}
```

### Missing/disabled application access — 403

```json
{
  "error": {
    "code": "ACCESS_DISABLED",
    "message": "Application access is not available",
    "requestId": "request-id"
  }
}
```

## Domain authorization

Unchanged:

- authenticated identity + active profile + required capability => execute;
- authenticated identity + active profile - required capability => `403 FORBIDDEN`;
- client-supplied role/capability values are ignored.

## Web auth port

The application session layer exposes provider-neutral behavior conceptually equivalent to:

```text
Session
- status
- principal
- refresh()
- signOut()
```

Sign-in UI ownership is delegated to Clerk's `<SignIn />` component rather than an application password method.

## Failure handling

- token refresh failure clears stale application authority;
- 401 from protected API triggers session refresh/unauthenticated handling rather than blind mutation retry;
- 403 ACCESS_DISABLED does not expose role/capability details;
- Clerk provider outage is distinguishable from an application capability denial in logs without leaking credentials.
