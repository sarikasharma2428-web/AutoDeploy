#!/bin/bash
set -e

ENVIRONMENT=${1:-prod}

echo "⏪ Rolling back deployment in $ENVIRONMENT..."

kubectl rollout undo deployment/backend -n repo-analyzer
kubectl rollout undo deployment/frontend -n repo-analyzer

echo "⏳ Waiting for rollback to complete..."
kubectl rollout status deployment/backend -n repo-analyzer
kubectl rollout status deployment/frontend -n repo-analyzer

echo "✅ Rollback completed!"
