#!/usr/bin/env bash
# Media files restore script for Tavern.
# Usage: bash deploy/scripts/restore-media.sh <backup_file.tar.gz>

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo "Example: $0 backups/tavern_media_20260101_120000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEDIA_DIR="${SCRIPT_DIR}/../../media"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "[$(date)] WARNING: This will overwrite media files in ${MEDIA_DIR}."
echo "Press Ctrl+C within 5 seconds to cancel..."
sleep 5

echo "[$(date)] Restoring media files from ${BACKUP_FILE}..."

mkdir -p "${MEDIA_DIR}"
tar -xzf "${BACKUP_FILE}" -C "$(dirname "${MEDIA_DIR}")"

echo "[$(date)] Media restore completed."
