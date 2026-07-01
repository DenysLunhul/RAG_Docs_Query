resource "aws_iam_role" "ec2_role" {
  name = "knowledge-base-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "ec2_policy" {
  name = "knowledge-base-ec2-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:*"]
        Resource = ["arn:aws:s3:::knowledge-base-docs-denys-lunhul/*",
                    "arn:aws:s3:::knowledge-base-docs-denys-lunhul"]
      },
      {
        Effect = "Allow"
        Action = ["bedrock:*"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["ecr:*"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["sagemaker:InvokeEndpoint"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "knowledge-base-ec2-profile"
  role = aws_iam_role.ec2_role.name
}