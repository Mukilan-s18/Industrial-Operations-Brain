variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "industrial-brain-cluster"
}

variable "db_password" {
  description = "Password for PostgreSQL RDS instance"
  type        = string
  sensitive   = true
}
