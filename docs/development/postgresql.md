# Local PostgreSQL development

The reference Fastify API can run with either the in-memory repository or PostgreSQL.

## In-memory mode

Run the API without `DATABASE_URL`:

```bash
pnpm --filter @cpxlabs-admin/api dev
```

This keeps local smoke tests and consumers of the starter independent from database setup. Authentication requiring persisted Better Auth sessions is exercised by the PostgreSQL reference topology rather than this lightweight mode.

## PostgreSQL mode

Start the reference database:

```bash
docker compose up -d postgres
```

Copy the environment template:

```bash
cp apps/api/.env.example apps/api/.env
```

Configure development-only values for `BETTER_AUTH_SECRET` and `SEED_AUTH_PASSWORD`, then apply committed migrations and seed reference data:

```bash
pnpm --filter @cpxlabs-admin/api db:migrate
pnpm --filter @cpxlabs-admin/api db:seed
```

Start the API:

```bash
pnpm --filter @cpxlabs-admin/api dev
```

The API loads `apps/api/.env` when present. Explicit process environment variables continue to take precedence.

## Persistence rules

- `CustomerRepository` remains the customer application boundary.
- `AccessProfileRepository` owns application role/status persistence.
- Fastify routes do not import Prisma.
- Prisma-generated types do not leave the API infrastructure layer.
- Better Auth owns identity/session/account persistence but does not own application capabilities.
- `InMemoryCustomerRepository` remains available for tests and lightweight demos.
- `PrismaCustomerRepository` is selected when `DATABASE_URL` is present.
- Schema migrations never insert demo/reference rows.
- `db:seed` is explicit and idempotent.
- Reference auth users are created only when seed auth environment values are configured.
- CI runs migrations and seeds against PostgreSQL 17 before integration and browser tests.

## Production

Production deployments should provide `DATABASE_URL` and authentication secrets through the platform secret/environment system and run:

```bash
pnpm --filter @cpxlabs-admin/api db:migrate
```

Do not run `db:seed` in production unless the application intentionally requires a separately reviewed provisioning procedure. The default reference users are development/test fixtures, not production accounts.
