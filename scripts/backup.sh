#!/bin/bash
set -e

BACKUP_DIR=${BACKUP_DIR:-./backups}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "💾 Creating backup..."

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
kubectl exec -n repo-analyzer deployment/postgres -- pg_dumpall -U analyzer > $BACKUP_DIR/postgres_$TIMESTAMP.sql

# Backup Qdrant
echo "Backing up Qdrant..."
kubectl exec -n repo-analyzer deployment/qdrant -- tar czf /tmp/qdrant_backup.tar.gz /qdrant/storage
kubectl cp repo-analyzer/$(kubectl get pod -n repo-analyzer -l app=qdrant -o jsonpath='{.items[0].metadata.name}'):/tmp/qdrant_backup.tar.gz $BACKUP_DIR/qdrant_$TIMESTAMP.tar.gz

# Upload to S3
echo "Uploading to S3..."
aws s3 cp $BACKUP_DIR/postgres_$TIMESTAMP.sql s3://repo-analyzer-backups/postgres/
aws s3 cp $BACKUP_DIR/qdrant_$TIMESTAMP.tar.gz s3://repo-analyzer-backups/qdrant/

echo "✅ Backup completed: $TIMESTAMP"
