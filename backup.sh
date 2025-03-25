#!/bin/bash

# Define paths
DB_FILE="receipts.db"
IMG_DIR="saved_images"
BACKUP_FILE="backup.tar.gz"
CHECKSUM_FILE="backup_checksum.txt"

# Compute new checksum
NEW_CHECKSUM=$(tar cf - "$DB_FILE" "$IMG_DIR" | sha256sum | awk '{print $1}')

# Check if checksum file exists
if [ -f "$CHECKSUM_FILE" ]; then
    OLD_CHECKSUM=$(cat "$CHECKSUM_FILE")
else
    OLD_CHECKSUM=""
fi

# Compare checksums
if [ "$NEW_CHECKSUM" != "$OLD_CHECKSUM" ]; then
    # Create a new backup
    tar czf "$BACKUP_FILE" "$DB_FILE" "$IMG_DIR"
    echo "$NEW_CHECKSUM" > "$CHECKSUM_FILE"
    echo "Backup updated: $BACKUP_FILE"
else
    echo "No changes detected. Backup not updated."
fi
