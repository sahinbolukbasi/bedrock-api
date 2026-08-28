data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "knowledge_corpus" {
  bucket = "${var.environment}-bedrock-corpus-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.environment
    Service     = "BedrockKnowledgeCorpus"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "s3_encrypt" {
  bucket = aws_s3_bucket.knowledge_corpus.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_dynamodb_table" "agent_memory_store" {
  name         = "${var.environment}-bedrock-agent-memory"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "fact_id"

  attribute {
    name = "session_id"
    type = "S"
  }
  attribute {
    name = "fact_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Environment = var.environment
    Service     = "BedrockStatefulMemory"
  }
}
