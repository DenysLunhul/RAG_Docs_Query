resource "aws_s3_bucket" "knowledge-base" {
  bucket = "knowledge-base-docs-denys-lunhul"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "knowledge-base" {
  bucket = aws_s3_bucket.knowledge-base.id

  rule {
    id     = "expire-after-30-days"
    status = "Enabled"

    filter {}

    expiration {
      days = 30
    }
  }
}