output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.main.id
}

output "public_ip" {
  description = "Public IP address"
  value       = aws_eip.main.public_ip
}

output "private_ip" {
  description = "Private IP address"
  value       = aws_instance.main.private_ip
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.instance.id
}
