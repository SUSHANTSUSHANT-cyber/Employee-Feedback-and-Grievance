#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ENV_FILE="${ROOT_DIR}/.env"

[ -f "$ENV_FILE" ] || {
    echo "Create ${ENV_FILE} from .env.example first."
    exit 1
}

set -a
source "$ENV_FILE"
set +a


BACKUP_DIR="${ROOT_DIR}/backups"

mkdir -p "$BACKUP_DIR"

export PGPASSWORD="$POSTGRES_PASSWORD"


BACKUP_FILE="${BACKUP_DIR}/employee_assistant_$(date +%F_%H%M%S).dump"


pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -Fc \
    "$POSTGRES_DB" \
    -f "$BACKUP_FILE"


echo "Backup created successfully:"
echo "$BACKUP_FILE"