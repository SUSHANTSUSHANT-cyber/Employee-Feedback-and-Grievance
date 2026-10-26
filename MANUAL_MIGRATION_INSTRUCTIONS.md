# Manual Migration Instructions

## Database Migration

Since automated scripts are experiencing connection issues, here are manual steps to apply the migration:

### Option 1: Using pgAdmin or any PostgreSQL GUI tool

1. Open your PostgreSQL client (pgAdmin, DBeaver, etc.)
2. Connect to database: `employee_assistant` on `localhost:5433`
3. Execute this SQL:

```sql
-- Add employeeCodeRequired boolean field to custom_categories table
BEGIN;

ALTER TABLE custom_categories
    ADD COLUMN IF NOT EXISTS "employeeCodeRequired" BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE custom_categories
    ALTER COLUMN "employeeCodeRequired" SET DEFAULT FALSE;

UPDATE custom_categories
SET "employeeCodeRequired" = FALSE
WHERE "employeeCodeRequired" IS NULL;

ALTER TABLE custom_categories
    ALTER COLUMN "employeeCodeRequired" SET NOT NULL;

COMMIT;
```

4. Verify with:
```sql
SELECT name, "employeeCodeRequired" FROM custom_categories ORDER BY name;
```

All existing categories should have `employeeCodeRequired = false`

### Option 2: Using command line (if psql is in PATH)

```powershell
$env:PGPASSWORD='EmployeeAssisstantDatabase@123'
psql -h localhost -p 5433 -U postgres -d employee_assistant -f database/migrations/20261005_category_employee_code_required.sql
```

### Option 3: Copy-paste the SQL file

The complete migration SQL is in:
`database/migrations/20261005_category_employee_code_required.sql`

Just copy the contents and execute in your SQL client.

## Verification

After running the migration, verify:

```sql
-- Check column exists
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'custom_categories'
  AND column_name = 'employeeCodeRequired';

-- Expected result:
-- column_name          | data_type | is_nullable | column_default
-- employeeCodeRequired | boolean   | NO          | false

-- Check existing categories
SELECT name, "employeeCodeRequired" 
FROM custom_categories 
ORDER BY name;

-- All should show: employeeCodeRequired = f (false)
```

## If Migration Already Applied

If you've already applied this migration, the `ADD COLUMN IF NOT EXISTS` syntax makes it safe to run again without errors.

## Next Steps After Migration

1. ✅ Database migration applied
2. Build frontend (see below)
3. Restart API server
4. Test in browser

---

See IMPLEMENTATION_EMPLOYEECODEREQUIRED.md for full documentation.
