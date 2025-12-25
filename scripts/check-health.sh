#!/bin/bash
set -e

NAMESPACE=${1:-repo-analyzer}

echo "🏥 Checking cluster health..."

# Check pod status
echo "📦 Pod Status:"
kubectl get pods -n $NAMESPACE

# Check deployments
echo ""
echo "🚀 Deployments:"
kubectl get deployments -n $NAMESPACE

# Check services
echo ""
echo "🔌 Services:"
kubectl get services -n $NAMESPACE

# Check resource usage
echo ""
echo "💻 Resource Usage:"
kubectl top nodes || echo "Metrics server not available"
kubectl top pods -n $NAMESPACE || echo "Metrics server not available"

# Check persistent volumes
echo ""
echo "💾 Persistent Volumes:"
kubectl get pvc -n $NAMESPACE

# Health check endpoints
echo ""
echo "🏥 Health Endpoints:"
for pod in $(kubectl get pods -n $NAMESPACE -l app=backend -o jsonpath='{.items[*].metadata.name}'); do
    echo "Checking $pod..."
    kubectl exec -n $NAMESPACE $pod -- curl -s http://localhost:8000/health || echo "Failed"
done

echo ""
echo "✅ Health check completed!"
