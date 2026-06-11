#!/bin/bash
BACKUP_DIR="/Users/hathi/erp-backups"
DATE=$(date +%Y-%m-%d)
mkdir -p "$BACKUP_DIR/$DATE"
cp /Users/hathi/erp-taller/db.sqlite3 "$BACKUP_DIR/$DATE/db.sqlite3"
cp -r /Users/hathi/erp-taller/media "$BACKUP_DIR/$DATE/"
tar -czf "$BACKUP_DIR/backup-$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"
rm -rf "$BACKUP_DIR/$DATE"
echo "Backup complete: backup-$DATE.tar.gz"
