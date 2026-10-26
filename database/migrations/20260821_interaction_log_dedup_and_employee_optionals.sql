-- Run this once against the target PostgreSQL database before deploying the
-- unique complaint-number index to an installation that already has duplicates.
-- It first records every row that will be removed in a local backup table.

BEGIN;

-- Verification query: run before COMMIT to see the exact proposed deletion set.
-- SELECT "complaintNumber", COUNT(*) AS duplicate_count
-- FROM interaction_logs
-- WHERE "complaintNumber" <> ''
-- GROUP BY "complaintNumber"
-- HAVING COUNT(*) > 1
-- ORDER BY duplicate_count DESC, "complaintNumber";
--
-- SELECT COUNT(*) AS total_rows,
--        COUNT(DISTINCT NULLIF("complaintNumber", '')) AS unique_non_empty_complaint_numbers,
--        COUNT(*) - COUNT(DISTINCT NULLIF("complaintNumber", '')) AS rows_not_accounted_for_by_non_empty_keys
-- FROM interaction_logs;

CREATE TABLE IF NOT EXISTS interaction_logs_duplicate_backup (
    LIKE interaction_logs INCLUDING DEFAULTS
);

WITH ranked AS (
    SELECT id,
           ROW_NUMBER() OVER (PARTITION BY "complaintNumber" ORDER BY id) AS duplicate_rank
    FROM interaction_logs
    WHERE "complaintNumber" <> ''
)
INSERT INTO interaction_logs_duplicate_backup
SELECT source.*
FROM interaction_logs AS source
JOIN ranked ON ranked.id = source.id
WHERE ranked.duplicate_rank > 1
  AND NOT EXISTS (
      SELECT 1 FROM interaction_logs_duplicate_backup AS backup
      WHERE backup.id = source.id
  );

-- Verification query: this is the number backed up and about to be deleted.
-- SELECT COUNT(*) AS rows_to_delete FROM interaction_logs_duplicate_backup;

DELETE FROM interaction_logs AS target
USING (
    SELECT id,
           ROW_NUMBER() OVER (PARTITION BY "complaintNumber" ORDER BY id) AS duplicate_rank
    FROM interaction_logs
    WHERE "complaintNumber" <> ''
) AS ranked
WHERE target.id = ranked.id
  AND ranked.duplicate_rank > 1;

-- Never group NULL/empty complaint numbers: they have no confirmed shared key.
CREATE UNIQUE INDEX IF NOT EXISTS interaction_logs_complaint_number_unique
ON interaction_logs ("complaintNumber")
WHERE "complaintNumber" <> '';

ALTER TABLE employees ALTER COLUMN "attendanceStatus" DROP NOT NULL;
ALTER TABLE employees ALTER COLUMN "checkInTime" DROP NOT NULL;
ALTER TABLE employees ALTER COLUMN "avatarSeed" DROP NOT NULL;

COMMIT;

-- Post-migration verification (expected duplicate_count result: no rows).
-- SELECT "complaintNumber", COUNT(*) AS duplicate_count
-- FROM interaction_logs
-- WHERE "complaintNumber" <> ''
-- GROUP BY "complaintNumber"
-- HAVING COUNT(*) > 1;
