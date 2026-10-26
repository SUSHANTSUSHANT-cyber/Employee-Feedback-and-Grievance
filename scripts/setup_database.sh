#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ENV_FILE="${ROOT_DIR}/.env"

[ -f "$ENV_FILE" ] || {
    echo "Create ${ENV_FILE} from .env.example first."
    exit 1
}

command -v psql >/dev/null || {
    echo "psql is required."
    exit 1
}

set -a
source "$ENV_FILE"
set +a


# PostgreSQL admin credentials used only for initial setup.
POSTGRES_ADMIN_USER="${POSTGRES_ADMIN_USER:-postgres}"

if [ -z "${POSTGRES_ADMIN_PASSWORD:-}" ]; then
    echo "POSTGRES_ADMIN_PASSWORD is required for database setup."
    exit 1
fi

export PGPASSWORD="$POSTGRES_ADMIN_PASSWORD"


# ==========================================
# CREATE APPLICATION USER IF IT DOES NOT EXIST
# ==========================================

USER_EXISTS=$(psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_ADMIN_USER" \
    -d postgres \
    -tAc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_USER}'"
)

if ! echo "$USER_EXISTS" | grep -q 1; then

    echo "Creating PostgreSQL user: $POSTGRES_USER"

    psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_ADMIN_USER" \
        -d postgres \
        -c "CREATE USER \"${POSTGRES_USER}\" WITH PASSWORD '${POSTGRES_PASSWORD}';"

fi


# ==========================================
# CREATE DATABASE IF IT DOES NOT EXIST
# ==========================================

DB_EXISTS=$(psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_ADMIN_USER" \
    -d postgres \
    -tAc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'"
)

if ! echo "$DB_EXISTS" | grep -q 1; then

    echo "Creating database: $POSTGRES_DB"

    psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_ADMIN_USER" \
        -d postgres \
        -c "CREATE DATABASE \"${POSTGRES_DB}\" OWNER \"${POSTGRES_USER}\";"

fi


# ==========================================
# APPLY DATABASE SCHEMA
# ==========================================

echo "Applying database schema..."

export PGPASSWORD="$POSTGRES_PASSWORD"

psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -f "${ROOT_DIR}/database/schema.sql"


echo "Database setup completed successfully."