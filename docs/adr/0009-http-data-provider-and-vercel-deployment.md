# ADR-009: HTTP DataProvider and Vercel deployment boundary

- Status: Accepted
- Date: 2026-09-08

## Context

The starter must deploy before a reference backend exists while proving that the frontend is not coupled to the in-memory demo implementation.

## Decision

1. Keep `DataProvider` as the generic CRUD boundary.
2. Add `HttpDataProvider` as a REST adapter, not as a domain abstraction.
3. Keep demo mode as the default so previews work without infrastructure.
4. Select the adapter through validated Vite environment variables.
5. Use the following HTTP shape:
   - `GET /api/:resource?page&pageSize&search&sort&direction&filter.<field>`
   - `GET /api/:resource/:id`
   - `POST /api/:resource`
   - `PATCH /api/:resource/:id`
   - `DELETE /api/:resource/:id`
6. List responses use `{ data, total }`.
7. Errors use `{ error: { code, message, details?, requestId? } }`.
8. Vercel deploys only `apps/web`; `/api/*` is reserved and excluded from SPA rewrites.
9. Prefer same-origin `/api` for the reference fullstack deployment. Separate origins remain a supported variation.

## Consequences

- Existing resources and TanStack Query hooks do not change when switching backends.
- Generic CRUD stays generic; domain workflows will continue to use explicit application services/use cases.
- Backend implementations must map their native errors to the stable error envelope.
- Authentication cookies can use `credentials: include` in the HTTP adapter.
- The upcoming Fastify API can implement this contract independently from the frontend.

## Non-goals

- OpenAPI generation is not introduced in this ADR.
- `DataProvider` does not become a universal RPC layer.
- The Vercel web project does not host business logic.
