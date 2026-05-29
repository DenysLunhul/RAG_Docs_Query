resource "aws_s3_bucket" "knowledge-base" {
  bucket = "knowledge-base-docs-denys-lunhul"
  
  lifecycle {
    prevent_destroy = true
  }
}