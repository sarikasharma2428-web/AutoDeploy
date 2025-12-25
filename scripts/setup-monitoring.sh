#!/bin/bash
set -e

echo "📊 Setting up monitoring stack..."

# Create monitoring namespace
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=admin123

# Apply custom ServiceMonitor
kubectl apply -f k8s/base/servicemonitor.yaml

# Get Grafana password
echo ""
echo "✅ Monitoring setup complete!"
echo "Grafana: http://localhost:3001"
echo "Username: admin"
echo "Password: admin123"
echo ""
echo "Port-forward Grafana:"
echo "kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80"
