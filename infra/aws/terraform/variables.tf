variable "project" {
  type        = string
  description = "Project/system name used for resource naming."
  default     = "enterprise-llm-adoption-kit"
}

variable "env" {
  type        = string
  description = "Environment name (dev/staging/prod)."
  default     = "dev"
}

variable "aws_region" {
  type        = string
  description = "AWS region."
  default     = "us-east-1"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
  default     = "10.30.0.0/16"
}

variable "backend_desired_count" {
  type        = number
  description = "Desired count for the backend ECS service."
  default     = 1
}

variable "backend_cpu" {
  type        = number
  description = "Fargate CPU units."
  default     = 512
}

variable "backend_memory" {
  type        = number
  description = "Fargate memory (MiB)."
  default     = 1024
}

variable "backend_container_port" {
  type        = number
  description = "Backend container port."
  default     = 8000
}

variable "backend_image" {
  type        = string
  description = "Container image URI for the backend (ECR image recommended)."
  default     = ""
}

variable "openai_api_key" {
  type        = string
  description = "Optional: OpenAI API key for LLM_PROVIDER=openai. Leave blank for stub/offline."
  default     = ""
  sensitive   = true
}

