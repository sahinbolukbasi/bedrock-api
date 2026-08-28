variable "environment" {
  type = string
}

variable "agent_name" {
  type    = string
  default = "enterprise-autonomous-agent"
}

variable "primary_model_id" {
  type    = string
  default = "anthropic.claude-3-7-sonnet-20250219-v1:0"
}

variable "execution_role_arn" {
  type = string
}

variable "guardrail_id" {
  type = string
}
