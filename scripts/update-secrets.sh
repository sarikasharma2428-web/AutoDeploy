#!/bin/bash
set -e

NAMESPACE=${1:-repo-analyzer}

echo "🔐 Updating Kubernetes secrets..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Load environment variables
source .env

# Create secret from .env
kubectl create secret generic app-secrets \
    --from-literal=DATABASE_URL="$DATABASE_URL" \
    --from-literal=REDIS_URL="$REDIS_URL" \
    --from-literal=AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    --namespace=$NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Secrets updated successfully!"
