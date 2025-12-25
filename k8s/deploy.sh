#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-autodeployx}"
BACKEND_IMAGE="${BACKEND_IMAGE:-ghcr.io/example/autodeployx-backend:latest}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-ghcr.io/example/autodeployx-frontend:latest}"

echo ">> Applying core manifests to namespace ${NAMESPACE}"
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
echo "!! Remember to create secrets from k8s/secret-template.yaml with real credentials"
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/qdrant-statefulset.yaml
kubectl apply -f k8s/ingress.yaml

echo ">> Updating images"
kubectl set image deployment/autodeployx-backend -n "${NAMESPACE}" backend="${BACKEND_IMAGE}"
kubectl set image deployment/autodeployx-frontend -n "${NAMESPACE}" frontend="${FRONTEND_IMAGE}"

echo ">> Current rollout status"
kubectl rollout status deployment/autodeployx-backend -n "${NAMESPACE}"
kubectl rollout status deployment/autodeployx-frontend -n "${NAMESPACE}"
kubectl rollout status statefulset/qdrant -n "${NAMESPACE}"
