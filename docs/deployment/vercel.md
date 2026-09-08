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

`vercel.json` rewrites application routes to `index.html`, while preserving `/api/*` for a future same-origin API/proxy.

## Data provider modes

The first deployment requires no backend:

```env
VITE_DATA_PROVIDER=demo
VITE_API_BASE_URL=/api
```

For an HTTP backend:

```env
VITE_DATA_PROVIDER=http
VITE_API_BASE_URL=https://api.example.com/api
```

The preferred production topology is same-origin (`/api`) behind the deployment edge/reverse proxy because it simplifies session cookies, CSRF policy, CORS and observability correlation. A separate API origin remains supported when required.

## Vercel project creation

1. Import `az1nn/cpxlabs-admin` from GitHub.
2. Set Root Directory to `apps/web`.
3. Confirm Vite is detected.
4. Deploy with demo mode first.
5. Verify direct navigation to `/customers`, `/customers/new` and `/customers/cus_001` resolves to the SPA.
6. Configure `VITE_DATA_PROVIDER=http` only after an API is available.

## Preview deployments

Every pull request can produce a Vercel preview. No secrets are required while demo mode is active.

When HTTP mode is enabled, configure `VITE_API_BASE_URL` independently for Preview and Production environments.

## Contract boundary

The web application never imports a backend implementation. It depends only on `DataProvider` plus the stable HTTP conventions documented in ADR-009. This allows the reference Fastify API to be introduced without changing resource screens.
