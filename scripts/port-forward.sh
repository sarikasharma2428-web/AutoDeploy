#!/bin/bash
set -e

SERVICE=${1}
NAMESPACE=${2:-repo-analyzer}

case $SERVICE in
    backend)
        echo "🔌 Port-forwarding backend..."
        kubectl port-forward svc/backend-service 8000:8000 -n $NAMESPACE
        ;;
    frontend)
        echo "🔌 Port-forwarding frontend..."
        kubectl port-forward svc/frontend-service 3000:80 -n $NAMESPACE
        ;;
    postgres)
        echo "🔌 Port-forwarding postgres..."
        kubectl port-forward svc/postgres-service 5432:5432 -n $NAMESPACE
        ;;
    redis)
        echo "🔌 Port-forwarding redis..."
        kubectl port-forward svc/redis-service 6379:6379 -n $NAMESPACE
        ;;
    qdrant)
        echo "🔌 Port-forwarding qdrant..."
        kubectl port-forward svc/qdrant-service 6333:6333 -n $NAMESPACE
        ;;
    prometheus)
        echo "🔌 Port-forwarding prometheus..."
        kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring
        ;;
    grafana)
        echo "🔌 Port-forwarding grafana..."
        kubectl port-forward svc/prometheus-grafana 3001:80 -n monitoring
        ;;
    *)
        echo "❌ Unknown service: $SERVICE"
        echo "Available services: backend, frontend, postgres, redis, qdrant, prometheus, grafana"
        exit 1
        ;;
esac
