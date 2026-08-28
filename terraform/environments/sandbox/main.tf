terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "Bedrock-AI-Gateway"
      ManagedBy   = "Terraform"
    }
  }
}

module "knowledge_base" {
  source      = "../../modules/knowledge_base"
  environment = var.environment
}

module "guardrails" {
  source      = "../../modules/bedrock_guardrails"
  environment = var.environment
}

module "iam" {
  source               = "../../modules/iam"
  environment          = var.environment
  github_repository    = var.github_repository
  knowledge_bucket_arn = module.knowledge_base.knowledge_bucket_arn
  dynamodb_table_arn   = module.knowledge_base.dynamodb_table_arn
}

module "agentcore" {
  source             = "../../modules/bedrock_agentcore"
  environment        = var.environment
  execution_role_arn = module.iam.agent_execution_role_arn
  guardrail_id       = module.guardrails.guardrail_id
}
