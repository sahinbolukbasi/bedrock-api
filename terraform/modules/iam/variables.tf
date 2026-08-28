variable "environment" {
  type        = string
  description = "Target environment name (sandbox, staging, production)"
}

variable "github_repository" {
  type        = string
  description = "GitHub organization/repository for OIDC assume role (e.g. sahinbolukbasi/bedrock-api)"
  default     = "sahinbolukbasi/bedrock-api"
}

variable "knowledge_bucket_arn" {
  type        = string
  description = "ARN of the Knowledge Base S3 bucket"
}

variable "dynamodb_table_arn" {
  type        = string
  description = "ARN of the Agent DynamoDB table"
}
