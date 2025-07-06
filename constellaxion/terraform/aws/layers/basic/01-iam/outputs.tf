output "iam_role_arn" {
  description = "The ARN of the created constellaxion-admin IAM role."
  value       = aws_iam_role.constellaxion_admin.arn
}

output "iam_role_name" {
  description = "The name of the created constellaxion-admin IAM role."
  value       = aws_iam_role.constellaxion_admin.name
}
