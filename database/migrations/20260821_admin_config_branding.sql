-- Idempotent repair for databases created before AdminConfig branding fields
-- were added to the SQLAlchemy model. No tables or existing rows are removed.
BEGIN;

ALTER TABLE admin_config
    ADD COLUMN IF NOT EXISTS "themeColor" TEXT NOT NULL DEFAULT '#173D72';

ALTER TABLE admin_config
    ADD COLUMN IF NOT EXISTS "logoName" TEXT NOT NULL DEFAULT 'aisin';

-- Also repair an earlier partial/manual migration without changing existing
-- non-null branding values.
ALTER TABLE admin_config
    ALTER COLUMN "themeColor" SET DEFAULT '#173D72',
    ALTER COLUMN "logoName" SET DEFAULT 'aisin';

UPDATE admin_config
SET "themeColor" = COALESCE("themeColor", '#173D72'),
    "logoName" = COALESCE("logoName", 'aisin')
WHERE "themeColor" IS NULL OR "logoName" IS NULL;

ALTER TABLE admin_config
    ALTER COLUMN "themeColor" SET NOT NULL,
    ALTER COLUMN "logoName" SET NOT NULL;

COMMIT;

-- Verification:
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'admin_config'
--   AND column_name IN ('themeColor', 'logoName')
-- ORDER BY column_name;
