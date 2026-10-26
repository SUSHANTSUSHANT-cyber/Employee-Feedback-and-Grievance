-- Adds one hashed-password master admin and opaque server-side sessions.
-- This migration does not modify any existing application data.
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    username TEXT NOT NULL UNIQUE CHECK (username = 'admin'),
    "passwordHash" TEXT NOT NULL,
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin_sessions (
    "tokenHash" TEXT PRIMARY KEY,
    "adminId" INTEGER NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
    "expiresAt" TIMESTAMPTZ NOT NULL,
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS admin_sessions_expires_at_idx
ON admin_sessions ("expiresAt");
