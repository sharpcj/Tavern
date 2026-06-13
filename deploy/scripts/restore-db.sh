#!/usr/bin/env bash
# Database restore script for Tavern.
# Usage: bash deploy/scripts/restore-db.sh <backup_file.sql.gz>

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo "Example: $0 backups/tavern_db_20260101_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Source environment variables from .env.prod if available
ENV_FILE="${SCRIPT_DIR}/../.env.prod"
if [ -f "${ENV_FILE}" ]; then
    set -a
    # shellcheck source=/dev/null
    source "${ENV_FILE}"
    set +a
fi

MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-tavern}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"
MYSQL_DATABASE="${MYSQL_DATABASE:-tavern}"

echo "[$(date)] WARNING: This will overwrite the database '${MYSQL_DATABASE}'."
echo "Press Ctrl+C within 5 seconds to cancel..."
sleep 5

echo "[$(date)] Restoring database from ${BACKUP_FILE}..."

gunzip -c "${BACKUP_FILE}" | mysql \
    -h "${MYSQL_HOST}" \
    -P "${MYSQL_PORT}" \
    -u "${MYSQL_USER}" \
    -p"${MYSQL_PASSWORD}" \
    "${MYSQL_DATABASE}"

echo "[$(date)] Database restore completed."
