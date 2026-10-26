#!/usr/bin/env bash

set -euo pipefail

[ "$#" -eq 1 ] || {
    echo "Usage: $0 backup.dump"
    exit 1
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ENV_FILE="${ROOT_DIR}/.env"
BACKUP_FILE="$1"

[ -f "$ENV_FILE" ] || {
    echo "Create ${ENV_FILE} from .env.example first."
    exit 1
}

[ -f "$BACKUP_FILE" ] || {
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
}

set -a
source "$ENV_FILE"
set +a

export PGPASSWORD="$POSTGRES_PASSWORD"

pg_restore \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --clean \
    --if-exists \
    "$BACKUP_FILE"

echo "Restore completed successfully."