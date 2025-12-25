#!/bin/bash
set -e

CLUSTER_NAME=${1:-repo-analyzer-cluster}
REGION=${2:-us-east-1}

echo "🚀 Initializing Kubernetes cluster: $CLUSTER_NAME"

# Check if k3s is installed
if command -v k3s &> /dev/null; then
    echo "✅ k3s detected - using local cluster"
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
else
    echo "☁️  Setting up EKS cluster..."
    
    # Create EKS cluster (if using AWS)
    eksctl create cluster \
        --name $CLUSTER_NAME \
        --region $REGION \
        --nodegroup-name standard-workers \
        --node-type t3.medium \
        --nodes 2 \
        --nodes-min 1 \
        --nodes-max 4 \
        --managed
    
    # Update kubeconfig
    aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION
fi

# Install NGINX Ingress Controller
echo "📦 Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for ingress controller to be ready
kubectl wait --namespace ingress-nginx \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=120s

# Install cert-manager
echo "🔐 Installing cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for cert-manager
kubectl wait --namespace cert-manager \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/instance=cert-manager \
    --timeout=120s

# Install metrics-server
echo "📊 Installing metrics-server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Create namespaces
echo "📁 Creating namespaces..."
kubectl create namespace repo-analyzer --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Label namespaces
kubectl label namespace repo-analyzer environment=production --overwrite
kubectl label namespace monitoring environment=production --overwrite

echo "✅ Cluster initialization completed!"
echo ""
echo "Next steps:"
echo "  1. Deploy application: make k8s-apply"
echo "  2. Setup monitoring: make monitoring"
echo "  3. Check status: kubectl get all -n repo-analyzer"
