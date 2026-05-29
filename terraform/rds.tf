resource "aws_db_instance" "knowledge_base" {
  db_name = "knowledge_base"
  identifier        = "database-1"
  instance_class    = "db.t3.micro"
  engine            = "postgres"
  engine_version    = "16.14"
  username          = "postgres"
  password          = var.db_password
  skip_final_snapshot = true
  storage_encrypted = true
  allocated_storage = 20
  storage_type      = "gp3"
  db_subnet_group_name = "rds-ec2-db-subnet-group-1"
  copy_tags_to_snapshot        = true
  max_allocated_storage        = 1000
  performance_insights_enabled = true

  vpc_security_group_ids = [
    data.aws_security_group.rds_ec2.id
  ]
}