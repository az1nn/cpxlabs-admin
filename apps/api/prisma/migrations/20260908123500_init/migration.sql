CREATE TABLE "customers" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "company" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT "customers_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "customers_email_key" ON "customers"("email");
CREATE INDEX "customers_name_idx" ON "customers"("name");
CREATE INDEX "customers_status_idx" ON "customers"("status");

INSERT INTO "customers" ("id", "name", "email", "company", "status", "updated_at") VALUES
  ('cus_001', 'Acme Brasil', 'ops@acme.example', 'Acme', 'active', '2026-09-08T12:12:00Z'),
  ('cus_002', 'Northstar Retail', 'admin@northstar.example', 'Northstar', 'lead', '2026-09-07T19:40:00Z');
