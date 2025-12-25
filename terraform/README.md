## Terraform Deployment

This stack provisions the minimum AWS resources needed to run AutoDeployX on a single EC2 instance with Docker Compose. It is intentionally sized for the free tier where possible.

### Resources

| Module | Resources |
| ------ | --------- |
| `modules/vpc` | 1 VPC, 2 subnets (public/private), routing + IGW |
| `modules/iam` | Instance profile with SSM + ECR access policy |
| `modules/ec2` | Single `t2.micro` instance + security group + Elastic IP |
| `modules/ecr` | ECR repositories for `backend` and `frontend` images |
| `modules/s3` | Versioned bucket for logs/artifacts |

### Usage

```bash
cd terraform
terraform init
terraform workspace select dev || terraform workspace new dev
terraform apply -var-file="environments/dev/terraform.tfvars"
```

### Billing considerations

- `t2.micro` is within the AWS free tier but running 24/7 still consumes the monthly quota. Larger instances incur on-demand charges.
- Elastic IPs incur cost when allocated without a running instance.
- ECR storage and data transfer are billed per GB.
- S3 buckets incur charges for storage, PUT/GET, and data transfer.
- VPC endpoints and NAT gateways are **not** provisioned; adding them would incur additional hourly charges.

Always destroy environments that are not in use:

```bash
terraform destroy -var-file="environments/dev/terraform.tfvars"
```
