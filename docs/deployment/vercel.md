# Vercel deployment

## Reference deployment

The web SPA is deployable as an independent Vercel project from the monorepo.

Configure the Vercel project with:

- Root Directory: `apps/web`
- Framework Preset: Vite
- Node.js: 22.x or newer compatible with the repository engine
- Install Command: provided by `apps/web/vercel.json`
- Build Command: provided by `apps/web/vercel.json`
- Output Directory: `dist`

`vercel.json` rewrites application routes to `index.html` while preserving `/api/*` for the reference API/reverse proxy.

## Demo deployment

A frontend-only preview remains available with no backend or secrets:

```env
VITE_DATA_PROVIDER=demo
VITE_AUTH_MODE=demo
VITE_API_BASE_URL=/api
```

Demo auth is an explicit showcase mode. It is not a fallback for failed server authentication and must not be used as a production security model.

## Server-authenticated deployment

For the reference enterprise topology:

```env
VITE_DATA_PROVIDER=http
VITE_AUTH_MODE=server
VITE_API_BASE_URL=/api
```

The preferred production topology keeps browser API calls same-origin (`/api`) behind the deployment edge/reverse proxy. The API environment must separately provide at least:

- `DATABASE_URL`
- `BETTER_AUTH_SECRET`
- `BETTER_AUTH_URL` using the externally reachable API/auth origin expected by Better Auth
- `APP_ORIGIN` matching the allowed SPA origin

Reference seed credentials are not production deployment secrets and `db:seed` must not be used as the production provisioning mechanism.

## Optional API telemetry

OpenTelemetry is disabled by default and is independent of domain/audit correctness. A deployment that uses an OTLP/HTTP collector can configure the API with:

```env
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=https://collector.example.com
OTEL_SERVICE_NAME=cpxlabs-admin-api
```

The API sends traces to `/v1/traces` and metrics to `/v1/metrics` beneath the configured base endpoint. The edge/proxy should preserve W3C trace headers when distributed tracing is required, but the application-owned `x-request-id` remains the stable correlation identifier exposed to API clients and stored in durable audit rows.

Do not route telemetry through the SPA/Vercel frontend project. Configure it in the API runtime environment.

## Session and proxy requirements

The browser relies on secure cookie sessions rather than browser-stored bearer tokens. The deployment edge must therefore preserve:

- request cookies from the SPA to `/api/*`;
- all `Set-Cookie` headers returned by the authentication API;
- `Host`/forwarded protocol information required to reconstruct the public request URL;
- same-origin semantics unless a separately reviewed CORS/CSRF/cookie design is introduced.

Do not rewrite `/api/*` to `index.html`. SPA fallback applies only to application routes.

## Vercel project creation

1. Import `az1nn/cpxlabs-admin` from GitHub.
2. Set Root Directory to `apps/web`.
3. Confirm Vite is detected.
4. Deploy with `VITE_DATA_PROVIDER=demo` and `VITE_AUTH_MODE=demo` for a frontend-only preview, or wire `/api` before enabling server mode.
5. Verify direct navigation to `/customers`, `/customers/new`, `/customers/cus_001`, and `/sign-in` resolves to the SPA.
6. For server mode, verify sign-in returns a cookie and `/api/session` succeeds after a full page reload.
7. Verify protected routes redirect to `/sign-in` after logout/revocation.
8. Verify API responses expose `x-request-id`; if OTLP is enabled, confirm the same id appears as `cpx.request_id` on Fastify spans.

## Preview deployments

Frontend-only preview deployments require no authentication secrets in demo mode.

A server-authenticated Preview requires an isolated API/database or another explicitly approved preview environment. Never point an untrusted preview deployment at production session infrastructure.

## Contract boundary

The web application does not trust Better Auth provider objects as application authority. It consumes the application-owned `/api/session` contract and server-derived capabilities. Better Auth remains replaceable identity/session infrastructure; Fastify remains authoritative for application authorization.
