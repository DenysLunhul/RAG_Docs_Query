data "aws_security_group" "ec2" {
  id = "sg-08e9b54dd8b7b5574"
}

data "aws_security_group" "ec2_rds" {
  id = "sg-09270ad522825d317"
}

data "aws_security_group" "rds_ec2" {
  id = "sg-0bbfb0add448736f4"
}

data "aws_security_group" "ec2_rds_1" {
  id = "sg-06190b48243af9b56"
}