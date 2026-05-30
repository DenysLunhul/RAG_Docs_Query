data "archive_file" "delete_chunks" {
  type        = "zip"
  source_file = "${path.module}/../lambda/delete_chunks.py"
  output_path = "${path.module}/../lambda/delete_chunks.zip"
}

resource "aws_iam_role" "lambda_role" {
  name = "knowledge-base-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "knowledge-base-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "delete_chunks" {
  function_name    = "delete-chunks-on-s3-remove"
  role             = aws_iam_role.lambda_role.arn
  handler          = "delete_chunks.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.delete_chunks.output_path
  source_code_hash = data.archive_file.delete_chunks.output_base64sha256
  timeout          = 30

  layers = [
    "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python312:16"
  ]

  vpc_config {
    subnet_ids = [
      "subnet-0ed5a418965d295d0",
      "subnet-0fb9c1b08646094be",
      "subnet-08440db65234b7f68",
      "subnet-03f45e00d024cf0c2",
      "subnet-0926986c06841a066"
    ]
    security_group_ids = [data.aws_security_group.rds_ec2.id]
  }

  environment {
    variables = {
      DB_HOST     = aws_db_instance.knowledge_base.address
      DB_PORT     = "5432"
      DB_NAME     = "knowledge_base"
      DB_USER     = "postgres"
      DB_PASSWORD = var.db_password
    }
  }
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.delete_chunks.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::knowledge-base-docs-denys-lunhul"
}

resource "aws_s3_bucket_notification" "delete_trigger" {
  bucket = aws_s3_bucket.knowledge-base.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.delete_chunks.arn
    events              = ["s3:ObjectRemoved:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

resource "aws_security_group_rule" "lambda_to_rds" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = data.aws_security_group.rds_ec2.id
  source_security_group_id = data.aws_security_group.rds_ec2.id
  description              = "Allow Lambda to connect to RDS"
}
