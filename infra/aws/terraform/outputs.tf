output "alb_dns_name" {
  description = "ALB DNS name (backend is reachable via http://<dns>/)."
  value       = aws_lb.main.dns_name
}

output "backend_ecr_repository" {
  description = "ECR repository URL for backend images."
  value       = aws_ecr_repository.backend.repository_url
}

output "frontend_assets_bucket" {
  description = "S3 bucket for frontend build artifacts (CloudFront recommended)."
  value       = aws_s3_bucket.frontend_assets.bucket
}

output "audit_exports_bucket" {
  description = "S3 bucket for audit exports / evidence packs."
  value       = aws_s3_bucket.audit_exports.bucket
}

