# Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (k3s/EKS)
- kubectl configured
- Terraform >= 1.6.0
- AWS CLI configured
- Helm 3.x

## Local Development

### Quick Start
```bash
make install
make dev
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### With Docker Compose
```bash
docker-compose -f docker/docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### 1. Setup Cluster
```bash
# Install k3s (local)
curl -sfL https://get.k3s.io | sh -

# Or configure EKS
aws eks update-kubeconfig --name repo-analyzer-cluster --region us-east-1
```

### 2. Deploy Application
```bash
# Deploy to dev
kubectl apply -k k8s/overlays/dev/

# Deploy to prod
kubectl apply -k k8s/overlays/prod/
```

### 3. Verify Deployment
```bash
./scripts/check-health.sh
```

## AWS Infrastructure (Terraform)

### 1. Initialize Terraform
```bash
cd terraform
terraform init
```

### 2. Plan Infrastructure
```bash
terraform plan -var-file=environments/prod/terraform.tfvars
```

### 3. Apply Infrastructure
```bash
terraform apply -var-file=environments/prod/terraform.tfvars
```

### 4. Get Outputs
```bash
terraform output
```

## CI/CD Pipeline

### GitHub Actions

Workflows are triggered automatically:
- `ci.yml` - On every push/PR
- `cd.yml` - On push to main or tags
- `destroy.yml` - Manual trigger only

### Required Secrets

Set in GitHub Repository Settings:
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
ECR_REGISTRY
SLACK_WEBHOOK
```

## Monitoring

### Setup Monitoring Stack
```bash
./scripts/setup-monitoring.sh
```

### Access Dashboards
```bash
# Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80
```

Credentials:
- Username: `admin`
- Password: `admin123`

## Backup & Restore

### Create Backup
```bash
./scripts/backup.sh
```

### Restore from Backup
```bash
./scripts/restore.sh <timestamp>
```

## Scaling

### Manual Scaling
```bash
kubectl scale deployment backend --replicas=5 -n repo-analyzer
```

### Auto Scaling (HPA)

Already configured in k8s/base/hpa.yaml:
- CPU threshold: 70%
- Memory threshold: 80%
- Min replicas: 2
- Max replicas: 10

## Troubleshooting

### View Logs
```bash
kubectl logs -f deployment/backend -n repo-analyzer
kubectl logs -f deployment/frontend -n repo-analyzer
```

### Debug Pod
```bash
kubectl exec -it deployment/backend -n repo-analyzer -- /bin/bash
```

### Check Events
```bash
kubectl get events -n repo-analyzer --sort-by='.lastTimestamp'
```

### Rollback Deployment
```bash
./scripts/rollback.sh prod
```

## Load Testing
```bash
./scripts/load-test.sh http://localhost:8000 50 300
```

## Cost Optimization (AWS Free Tier)

### Staying Free

- 1x t2.micro EC2 instance (750 hours/month free)
- 30GB EBS storage
- 5GB S3 storage
- 500MB ECR storage
- No NAT Gateway (use public subnets)
- No ALB (use NodePort)

### Monthly Costs (if exceeding free tier)

- t2.micro: ~$8.50/month
- EBS (30GB): ~$3/month
- Data transfer: Variable

## Security Best Practices

1. **Secrets Management**
   - Use AWS Secrets Manager
   - Never commit secrets to Git
   - Rotate credentials regularly

2. **Network Security**
   - Restrict security group rules
   - Use private subnets when possible
   - Enable VPC Flow Logs

3. **Image Security**
   - Scan images with Trivy
   - Use minimal base images
   - Update regularly

4. **Access Control**
   - Use IAM roles (not keys)
   - Follow principle of least privilege
   - Enable MFA for AWS

## Performance Tuning

### Backend
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Database
```sql
-- Optimize PostgreSQL
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
```

### Caching

Redis cache configured for:
- Job status: 5 minutes
- Analysis results: 1 hour
- Repository metadata: 30 minutes

## Monitoring Metrics

### Key Metrics

- Request rate: `rate(http_requests_total[5m])`
- Error rate: `rate(http_requests_total{status=~"5.."}[5m])`
- Latency p95: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- CPU usage: `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- Memory usage: `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100`

## Support

For issues or questions:
- Check logs: `kubectl logs -f deployment/backend -n repo-analyzer`
- View metrics: http://localhost:9090
- Check dashboards: http://localhost:3001
- Health endpoint: http://localhost:8000/health
