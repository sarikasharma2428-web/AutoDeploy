#!/bin/bash
set -e

COMPONENT=${1}
REPLICAS=${2}
NAMESPACE=${3:-repo-analyzer}

if [ -z "$COMPONENT" ] || [ -z "$REPLICAS" ]; then
    echo "Usage: ./scale.sh <component> <replicas> [namespace]"
    echo "Example: ./scale.sh backend 5 repo-analyzer"
    exit 1
fi

echo "📈 Scaling $COMPONENT to $REPLICAS replicas..."

kubectl scale deployment/$COMPONENT --replicas=$REPLICAS -n $NAMESPACE

echo "⏳ Waiting for rollout..."
kubectl rollout status deployment/$COMPONENT -n $NAMESPACE

echo "✅ Scaling completed!"
kubectl get deployment $COMPONENT -n $NAMESPACE
