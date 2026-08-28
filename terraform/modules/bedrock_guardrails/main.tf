resource "aws_bedrock_guardrail" "guardrail" {
  name        = "${var.environment}-bedrock-guardrail"
  description = "PII anonymization, prompt injection defense, and content moderation"

  blocked_input_messaging   = "Güvenlik politikası: İstek içerik kurallarına uymadığı için sınırlandırıldı."
  blocked_outputs_messaging  = "Güvenlik politikası: Üretilen yanıt içerik filtreleri tarafından engellendi."

  content_policy_config {
    filters_config {
      type            = "HATE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "VIOLENCE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "PROMPT_ATTACK"
      input_strength  = "HIGH"
      output_strength = "NONE"
    }
  }

  sensitive_information_policy_config {
    pii_entities_config {
      type   = "CREDIT_DEBIT_CARD_NUMBER"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "EMAIL"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "PHONE"
      action = "ANONYMIZE"
    }
  }
}
