# ADR-010: Fastify reference API as optional modular monolith

- Status: Accepted
- Date: 2026-09-08

## Decision

Provide `apps/api` as the TypeScript reference backend using Fastify 5.

The API is optional: `apps/web` remains compatible with external .NET, Python, Java or other backends that implement the HTTP contract.

The initial module proves:

- `/health`
- customer list/search/filter/sort/pagination
- create/show/edit/delete
- request validation with Fastify JSON Schema
- response serialization schemas for safe DTO output
- stable error envelope with request correlation id
- testability through `fastify.inject()`

The initial persistence adapter is intentionally in-memory. PostgreSQL and an ORM/repository adapter are a separate decision.

## Boundary

```text
HTTP route
  -> application/use case (introduced when domain behavior requires it)
    -> repository contract
      -> infrastructure adapter
```

Straightforward CRUD may remain thin while there is no domain behavior to justify an application service. Non-CRUD workflows must not be hidden in generic repository updates.

## Deployment

Vercel currently deploys only `apps/web`. The Fastify service is not coupled to Vercel and can be deployed independently. A future edge/reverse-proxy layer can expose it under same-origin `/api`.
