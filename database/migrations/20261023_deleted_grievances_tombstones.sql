-- Migration: 20261023_deleted_grievances_tombstones.sql
-- Purpose: Create tombstone table for deleted grievances to prevent resurrection
--          and enable synchronization of deletions to Android devices.

BEGIN;

CREATE TABLE IF NOT EXISTS deleted_grievances (
    "complaintNumber" TEXT PRIMARY KEY,
    "deletedAt" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS deleted_grievances_deleted_at_idx
ON deleted_grievances ("deletedAt");

COMMIT;
