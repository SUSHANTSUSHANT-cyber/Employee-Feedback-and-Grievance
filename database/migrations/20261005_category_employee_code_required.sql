-- Add employeeCodeRequired boolean field to custom_categories table
-- This is required by the Android application's category-level employee verification feature.
-- Android Room database migration version 13 already expects this field.

BEGIN;

-- Add the column with default FALSE for all existing categories
ALTER TABLE custom_categories
    ADD COLUMN IF NOT EXISTS "employeeCodeRequired" BOOLEAN NOT NULL DEFAULT FALSE;

-- Ensure the default is set properly
ALTER TABLE custom_categories
    ALTER COLUMN "employeeCodeRequired" SET DEFAULT FALSE;

-- Update any NULL values to FALSE (shouldn't be any, but defensive)
UPDATE custom_categories
SET "employeeCodeRequired" = FALSE
WHERE "employeeCodeRequired" IS NULL;

-- Ensure NOT NULL constraint
ALTER TABLE custom_categories
    ALTER COLUMN "employeeCodeRequired" SET NOT NULL;

COMMIT;

-- Verification:
-- SELECT name, "employeeCodeRequired" 
-- FROM custom_categories 
-- ORDER BY name;
