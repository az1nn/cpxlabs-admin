# Local PostgreSQL development

The reference Fastify API can run with either the in-memory repository or PostgreSQL.

## In-memory mode

Run the API without `DATABASE_URL`:

```bash
pnpm --filter @cpxlabs-admin/api dev
```

This keeps local smoke tests and consumers of the starter independent from database setup.

## PostgreSQL mode

Start the reference database:

```bash
docker compose up -d postgres
```

Copy the environment template:

```bash
cp apps/api/.env.example apps/api/.env
```

Apply committed migrations and seed reference data:

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

- `CustomerRepository` is the application boundary.
- Fastify routes do not import Prisma.
- Prisma-generated types do not leave the API infrastructure layer.
- `InMemoryCustomerRepository` remains available for tests and lightweight demos.
- `PrismaCustomerRepository` is selected when `DATABASE_URL` is present.
- Schema migrations never insert demo/reference rows.
- `db:seed` is explicit and idempotent.
- CI runs migrations and seeds against PostgreSQL 17 before integration and browser tests.

## Production

Production deployments should provide `DATABASE_URL` through the platform secret/environment system and run:

```bash
pnpm --filter @cpxlabs-admin/api db:migrate
```

Do not run `db:seed` in production unless the application intentionally requires the reference dataset.
