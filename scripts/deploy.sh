#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
VERSION=${2:-latest}

echo "🚀 Deploying RepoAnalyzer to $ENVIRONMENT..."

# Build Docker images
echo "📦 Building Docker images..."
docker build -f docker/Dockerfile.backend -t repo-analyzer-backend:$VERSION .
docker build -f docker/Dockerfile.frontend -t repo-analyzer-frontend:$VERSION .

# Tag images for ECR
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REGISTRY=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker tag repo-analyzer-backend:$VERSION $ECR_REGISTRY/repo-analyzer-backend:$VERSION
docker tag repo-analyzer-frontend:$VERSION $ECR_REGISTRY/repo-analyzer-frontend:$VERSION

# Push to ECR
echo "📤 Pushing images to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
docker push $ECR_REGISTRY/repo-analyzer-backend:$VERSION
docker push $ECR_REGISTRY/repo-analyzer-frontend:$VERSION

# Deploy to Kubernetes
echo "☸️  Deploying to Kubernetes..."
kubectl apply -k k8s/overlays/$ENVIRONMENT/
kubectl set image deployment/backend backend=$ECR_REGISTRY/repo-analyzer-backend:$VERSION -n repo-analyzer
kubectl set image deployment/frontend frontend=$ECR_REGISTRY/repo-analyzer-frontend:$VERSION -n repo-analyzer

# Wait for rollout
echo "⏳ Waiting for deployment to complete..."
kubectl rollout status deployment/backend -n repo-analyzer --timeout=5m
kubectl rollout status deployment/frontend -n repo-analyzer --timeout=5m

# Run health check
echo "🏥 Running health check..."
kubectl port-forward svc/backend-service 8000:8000 -n repo-analyzer &
sleep 5
if curl -f http://localhost:8000/health; then
    echo "✅ Deployment successful!"
else
    echo "❌ Health check failed!"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
