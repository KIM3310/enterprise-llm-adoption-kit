resource "aws_s3_bucket" "frontend_assets" {
  bucket = "${local.name}-${data.aws_caller_identity.current.account_id}-frontend"
  tags   = local.tags
}

resource "aws_s3_bucket_public_access_block" "frontend_assets" {
  bucket                  = aws_s3_bucket.frontend_assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend_assets" {
  bucket = aws_s3_bucket.frontend_assets.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket" "audit_exports" {
  bucket = "${local.name}-${data.aws_caller_identity.current.account_id}-audit"
  tags   = local.tags
}

resource "aws_s3_bucket_public_access_block" "audit_exports" {
  bucket                  = aws_s3_bucket.audit_exports.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "audit_exports" {
  bucket = aws_s3_bucket.audit_exports.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

