environment    = "prod"
instance_type  = "t2.micro"
aws_region     = "us-east-1"
project_name   = "repo-analyzer"
s3_bucket_name = "repo-analyzer-storage-prod"

vpc_cidr = "10.1.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

enable_monitoring = true
