output "knowledge_bucket_name" {
  value       = aws_s3_bucket.knowledge_corpus.bucket
}

output "knowledge_bucket_arn" {
  value       = aws_s3_bucket.knowledge_corpus.arn
}

output "dynamodb_table_name" {
  value       = aws_dynamodb_table.agent_memory_store.name
}

output "dynamodb_table_arn" {
  value       = aws_dynamodb_table.agent_memory_store.arn
}
