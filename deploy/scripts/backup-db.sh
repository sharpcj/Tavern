#!/usr/bin/env bash
# Database backup script for Tavern.
# Usage: bash deploy/scripts/backup-db.sh
# Requires: mysqldump, gzip

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/../backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/tavern_db_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=7

mkdir -p "${BACKUP_DIR}"

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

echo "[$(date)] Starting database backup for ${MYSQL_DATABASE}..."

mysqldump \
    -h "${MYSQL_HOST}" \
    -P "${MYSQL_PORT}" \
    -u "${MYSQL_USER}" \
    -p"${MYSQL_PASSWORD}" \
    --single-transaction \
    --routines \
    --triggers \
    --set-gtid-purged=OFF \
    "${MYSQL_DATABASE}" | gzip > "${BACKUP_FILE}"

echo "[$(date)] Backup created: ${BACKUP_FILE}"

# Clean up old backups
find "${BACKUP_DIR}" -name "tavern_db_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Cleaned up backups older than ${RETENTION_DAYS} days."
echo "[$(date)] Backup completed."
