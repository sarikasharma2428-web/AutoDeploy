output "role_arn" {
  description = "IAM role ARN"
  value       = aws_iam_role.ec2_role.arn
}

output "role_name" {
  description = "IAM role name"
  value       = aws_iam_role.ec2_role.name
}

output "instance_profile_name" {
  description = "Instance profile name"
  value       = aws_iam_instance_profile.ec2_profile.name
}

output "instance_profile_arn" {
  description = "Instance profile ARN"
  value       = aws_iam_instance_profile.ec2_profile.arn
}
