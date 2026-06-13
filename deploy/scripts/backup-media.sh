#!/usr/bin/env bash
# Media files backup script for Tavern.
# Usage: bash deploy/scripts/backup-media.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/../backups"
MEDIA_DIR="${SCRIPT_DIR}/../../media"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/tavern_media_${TIMESTAMP}.tar.gz"
RETENTION_DAYS=7

mkdir -p "${BACKUP_DIR}"

if [ ! -d "${MEDIA_DIR}" ]; then
    echo "[$(date)] Media directory not found: ${MEDIA_DIR}, skipping."
    exit 0
fi

echo "[$(date)] Starting media backup..."

tar -czf "${BACKUP_FILE}" -C "$(dirname "${MEDIA_DIR}")" "$(basename "${MEDIA_DIR}")"

echo "[$(date)] Backup created: ${BACKUP_FILE}"

# Clean up old backups
find "${BACKUP_DIR}" -name "tavern_media_*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Cleaned up backups older than ${RETENTION_DAYS} days."
echo "[$(date)] Backup completed."
