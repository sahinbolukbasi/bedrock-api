output "guardrail_id" {
  value       = aws_bedrock_guardrail.guardrail.guardrail_id
  description = "ID of the created Bedrock Guardrail"
}

output "guardrail_arn" {
  value       = aws_bedrock_guardrail.guardrail.guardrail_arn
  description = "ARN of the created Bedrock Guardrail"
}
