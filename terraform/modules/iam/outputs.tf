output "agent_execution_role_arn" {
  value       = aws_iam_role.bedrock_agent_execution_role.arn
  description = "ARN of the Bedrock Agent Execution Role"
}
