# Quickstart: Clerk Authentication

## 1. Clerk development application

Create/select a Clerk development instance.

Required keys:

- publishable key for the Vite web app;
- secret key for the Fastify API.

For the enterprise reference deployment, configure Clerk so public sign-up is disabled or otherwise restricted according to the deployment's provisioning policy.

## 2. Environment

### `apps/web/.env`

```dotenv
VITE_DATA_PROVIDER=http
VITE_API_BASE_URL=/api
VITE_AUTH_MODE=server
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

### `apps/api/.env`

```dotenv
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/cpxlabs_admin
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
APP_ORIGIN=http://127.0.0.1:4173
```

Never commit real keys.

## 3. Database migration

```bash
pnpm --filter @cpxlabs-admin/api db:generate
pnpm --filter @cpxlabs-admin/api db:migrate
```

The migration preserves application access profiles while removing Better Auth provider tables.

## 4. Provision access

Create/provision the user in Clerk, obtain the Clerk user ID (`user_...`), and create/update the corresponding application `AccessProfile` with one of:

- `admin`
- `manager`
- `viewer`

The Clerk identity alone grants no application capability.

## 5. Run

```bash
pnpm dev
```

Open the web application and navigate to a protected route. The app redirects to `/sign-in`, Clerk completes authentication, and the application returns to the protected route after `/api/session` resolves the current Principal.

## 6. Verify

Repository deterministic gates:

```bash
pnpm typecheck
pnpm test
pnpm build
pnpm test:storybook
pnpm e2e
```

Live Clerk verification additionally requires valid Clerk development credentials and a provisioned test identity. That external gate is tracked as `CLERK-LIVE-INTEGRATION`.
