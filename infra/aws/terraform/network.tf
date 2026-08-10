module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.6"

  name = local.name
  cidr = var.vpc_cidr

  azs             = local.azs
  public_subnets  = [for idx in range(length(local.azs)) : cidrsubnet(var.vpc_cidr, 8, idx)]
  private_subnets = [for idx in range(length(local.azs)) : cidrsubnet(var.vpc_cidr, 8, idx + 10)]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = local.tags
}

