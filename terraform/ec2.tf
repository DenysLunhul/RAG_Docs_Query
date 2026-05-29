resource "aws_instance" "knowledge_base" {
  ami           = "ami-05cf1e9f73fbad2e2"
  instance_type = "t3.micro"

  vpc_security_group_ids = [
    data.aws_security_group.ec2.id,
    data.aws_security_group.ec2_rds.id,
    "sg-06190b48243af9b56"
  ]

  tags = {
    Name = "knowledge-base-server"
  }
}
