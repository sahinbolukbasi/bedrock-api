data "aws_caller_identity" "current" {}

resource "aws_iam_role" "bedrock_agent_execution_role" {
  name = "${var.environment}-bedrock-agent-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "bedrock_agent_least_privilege_policy" {
  name        = "${var.environment}-bedrock-agent-least-privilege"
  description = "Least privilege policy for AWS Bedrock models, S3 corpus, and DynamoDB memory"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockModelInvocation"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:Converse",
          "bedrock:ConverseStream"
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-7-sonnet-20250219-v1:0",
          "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-haiku-20241022-v1:0",
          "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0",
          "arn:aws:bedrock:*::foundation-model/amazon.nova-micro-v1:0"
        ]
      },
      {
        Sid    = "S3KnowledgeCorpusAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.knowledge_bucket_arn,
          "${var.knowledge_bucket_arn}/*"
        ]
      },
      {
        Sid    = "DynamoDBMemoryAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          var.dynamodb_table_arn,
          "${var.dynamodb_table_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_agent_policy" {
  role       = aws_iam_role.bedrock_agent_execution_role.name
  policy_arn = aws_iam_policy.bedrock_agent_least_privilege_policy.arn
}
