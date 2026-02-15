data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name = "${var.project}-${var.env}"

  tags = {
    Project     = var.project
    Environment = var.env
    ManagedBy   = "terraform"
    Repo        = "KIM3310/enterprise-llm-adoption-kit"
  }

  azs = slice(data.aws_availability_zones.available.names, 0, 2)

  llm_provider = var.openai_api_key != "" ? "openai" : "stub"
}
