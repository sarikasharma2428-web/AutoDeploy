#!/bin/bash

COMPONENT=${1:-backend}
NAMESPACE=${2:-repo-analyzer}
LINES=${3:-100}

echo "📋 Fetching logs for $COMPONENT..."

if [ "$COMPONENT" == "all" ]; then
    kubectl logs -f -l app.kubernetes.io/name=repo-analyzer -n $NAMESPACE --tail=$LINES --max-log-requests=10
else
    kubectl logs -f deployment/$COMPONENT -n $NAMESPACE --tail=$LINES
fi
