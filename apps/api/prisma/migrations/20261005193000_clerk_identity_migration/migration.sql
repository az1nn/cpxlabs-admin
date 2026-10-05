-- Feature 020: Clerk becomes the identity/session provider.
-- Preserve application-owned access_profiles while removing the Better Auth FK/tables.

ALTER TABLE "access_profiles"
  DROP CONSTRAINT IF EXISTS "access_profiles_user_id_fkey";

DROP TABLE IF EXISTS "session";
DROP TABLE IF EXISTS "account";
DROP TABLE IF EXISTS "verification";
DROP TABLE IF EXISTS "user";
