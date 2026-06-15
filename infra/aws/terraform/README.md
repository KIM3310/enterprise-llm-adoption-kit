# Terraform (AWS) - Draft IaC Reference
This folder contains a **draft** Terraform configuration that matches the conceptual design in:
- `docs/architecture/aws_openai_reference_architecture.md`

Notes:
- This is **not** a production module. It is a reference scaffold for operators.
- Defaults are conservative and avoid embedding secrets in code.
- You should use remote state (S3 + DynamoDB) for any real environment.

## What It Creates (Draft)
- VPC (public + private subnets across 2 AZs) via a standard module
- ALB (HTTP) + security groups
- ECS Fargate cluster + backend service (port 8000 behind ALB)
- ECR repository for backend images
- S3 buckets (frontend assets, audit exports)
- Secrets Manager secret placeholder for `LLM_OPENAI_API_KEY` (value optional)

## What It Intentionally Does NOT Create
- HTTPS certificates / custom domain (ACM + Route53)
- WAF rules (beyond being “recommended”)
- RDS (left as a future step for a real environment)
- CloudFront distribution (recommended in docs; omitted from this draft to keep IaC readable)

## Prereqs
- Terraform >= 1.5
- AWS credentials configured locally (or via `AWS_PROFILE`)

## Quick Start (For Architecture Only)
```bash
cd infra/aws/terraform
terraform init
terraform plan -out tfplan
```

If you want to populate the OpenAI secret (optional):
```bash
terraform plan -var 'openai_api_key=YOUR_KEY' -out tfplan
```

## Variables
See `variables.tf`.

## Outputs
- `alb_dns_name`: where the backend is reachable (HTTP)

