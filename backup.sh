#!/bin/bash

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Change to script directory
cd "$SCRIPT_DIR" || exit 1  # Exit if cd fails

# Define paths (relative to script directory)
DB_FILE="receipts.db"
IMG_DIR="saved_images"
BACKUP_DIR="/media/peter/backups"
CHECKSUM_FILE="backup_checksum.txt"
EXTRACT_DIR="temp"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Get current date and time
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

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
    # Create a new backup (preserves relative paths)
    tar czf "$BACKUP_FILE" "$DB_FILE" "$IMG_DIR"
    echo "$NEW_CHECKSUM" > "$CHECKSUM_FILE"
    echo "Backup created: $BACKUP_FILE"

    # Ensure extract directory exists
    mkdir -p "$EXTRACT_DIR"

    # Extract into temp directory (preserves relative paths)
    tar xzf "$BACKUP_FILE" -C "$EXTRACT_DIR"
    echo "Backup extracted to $EXTRACT_DIR"
else
    echo "No changes detected. Backup not updated."
fi
