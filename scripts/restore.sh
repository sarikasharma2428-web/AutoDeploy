#!/bin/bash
set -e

BACKUP_TIMESTAMP=${1}

if [ -z "$BACKUP_TIMESTAMP" ]; then
    echo "Usage: ./restore.sh <backup_timestamp>"
    exit 1
fi

echo "♻️  Restoring from backup: $BACKUP_TIMESTAMP"

# Download from S3
aws s3 cp s3://repo-analyzer-backups/postgres/postgres_$BACKUP_TIMESTAMP.sql ./backups/
aws s3 cp s3://repo-analyzer-backups/qdrant/qdrant_$BACKUP_TIMESTAMP.tar.gz ./backups/

# Restore PostgreSQL
echo "Restoring PostgreSQL..."
kubectl exec -i -n repo-analyzer deployment/postgres -- psql -U analyzer < ./backups/postgres_$BACKUP_TIMESTAMP.sql

# Restore Qdrant
echo "Restoring Qdrant..."
kubectl cp ./backups/qdrant_$BACKUP_TIMESTAMP.tar.gz repo-analyzer/$(kubectl get pod -n repo-analyzer -l app=qdrant -o jsonpath='{.items[0].metadata.name}'):/tmp/
kubectl exec -n repo-analyzer deployment/qdrant -- tar xzf /tmp/qdrant_$BACKUP_TIMESTAMP.tar.gz -C /

echo "✅ Restore completed!"
