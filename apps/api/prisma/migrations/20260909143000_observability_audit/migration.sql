CREATE TABLE "audit_events" (
  "id" TEXT NOT NULL,
  "actor_id" TEXT NOT NULL,
  "actor_email" TEXT NOT NULL,
  "actor_name" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "subject_type" TEXT NOT NULL,
  "subject_id" TEXT NOT NULL,
  "before" JSONB,
  "after" JSONB,
  "correlation_id" TEXT NOT NULL,
  "tenant_id" TEXT,
  "occurred_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT "audit_events_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "audit_events_occurred_at_id_idx" ON "audit_events"("occurred_at", "id");
CREATE INDEX "audit_events_actor_id_occurred_at_idx" ON "audit_events"("actor_id", "occurred_at");
CREATE INDEX "audit_events_action_occurred_at_idx" ON "audit_events"("action", "occurred_at");
CREATE INDEX "audit_events_subject_type_subject_id_occurred_at_idx" ON "audit_events"("subject_type", "subject_id", "occurred_at");
CREATE INDEX "audit_events_correlation_id_idx" ON "audit_events"("correlation_id");
