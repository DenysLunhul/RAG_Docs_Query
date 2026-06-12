resource "aws_instance" "knowledge_base" {
  ami           = "ami-05cf1e9f73fbad2e2"
  instance_type = "t3.micro"
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
  user_data_replace_on_change = true
  key_name = "knowledge-base-key"

  vpc_security_group_ids = [
    data.aws_security_group.ec2.id,
    data.aws_security_group.ec2_rds.id,
    "sg-06190b48243af9b56"
  ]

  user_data = <<EOF
  #!/bin/bash
  apt-get update -y
  apt-get install -y ca-certificates curl gnupg

  # Docker
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | tee /etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io postgresql-client

  # AWS CLI
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  apt-get install -y unzip
  unzip awscliv2.zip
  ./aws/install

  systemctl start docker
  systemctl enable docker

  aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 287528889753.dkr.ecr.us-east-1.amazonaws.com
  docker pull 287528889753.dkr.ecr.us-east-1.amazonaws.com/knowledge-base:latest

  cat > /home/ubuntu/.env << 'ENVEOF'
S3_BUCKET_NAME=knowledge-base-docs-denys-lunhul
BEDROCK_MODEL_ID=arn:aws:bedrock:us-east-1:287528889753:inference-profile/global.anthropic.claude-haiku-4-5-20251001-v1:0
DATABASE_URL=postgresql://postgres:${var.db_password}@${aws_db_instance.knowledge_base.address}:5432/knowledge_base
AWS_DEFAULT_REGION=us-east-1
ENVEOF

  docker run -d --env-file /home/ubuntu/.env -p 8000:8000 --name knowledge-base 287528889753.dkr.ecr.us-east-1.amazonaws.com/knowledge-base:latest

  until PGPASSWORD=${var.db_password} psql -h ${aws_db_instance.knowledge_base.address} -U postgres -d knowledge_base -c "SELECT 1" > /dev/null 2>&1; do
    echo "Waiting for RDS..."
    sleep 5
  done
  PGPASSWORD=${var.db_password} psql -h ${aws_db_instance.knowledge_base.address} -U postgres -d knowledge_base -c "CREATE EXTENSION IF NOT EXISTS vector;"
  docker exec knowledge-base python -m app.models.init_db
EOF

  tags = {
    Name = "knowledge-base-server"
  }
}

resource "aws_eip" "knowledge_base" {
  instance = aws_instance.knowledge_base.id
  domain   = "vpc"

  tags = {
    Name = "knowledge-base-eip"
  }
}

output "ec2_public_ip" {
  value = aws_eip.knowledge_base.public_ip
}
