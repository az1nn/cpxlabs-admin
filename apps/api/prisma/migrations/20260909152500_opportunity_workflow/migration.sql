CREATE TYPE "opportunity_stage" AS ENUM ('qualification', 'discovery', 'proposal', 'negotiation', 'won', 'lost');

CREATE TABLE "opportunities" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "account_name" TEXT NOT NULL,
  "amount_minor" BIGINT NOT NULL,
  "currency" CHAR(3) NOT NULL,
  "expected_close_date" DATE NOT NULL,
  "stage" "opportunity_stage" NOT NULL DEFAULT 'qualification',
  "version" INTEGER NOT NULL DEFAULT 1,
  "loss_reason" TEXT,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "opportunities_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "opportunities_stage_idx" ON "opportunities"("stage");
CREATE INDEX "opportunities_expected_close_date_idx" ON "opportunities"("expected_close_date");
CREATE INDEX "opportunities_updated_at_idx" ON "opportunities"("updated_at");
CREATE INDEX "opportunities_account_name_idx" ON "opportunities"("account_name");
