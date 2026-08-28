import re
from typing import Dict, Any, Tuple, Optional
from loguru import logger


class EnterpriseGuardrailService:
    """
    AWS Bedrock Guardrails & In-Process Content Moderation Filter.
    
    1. Detects and neutralizes Prompt Injection / Jailbreak attacks.
    2. Anonymizes PII (Credit card numbers, Email addresses, Phone numbers).
    3. Enforces policy controls and safety boundaries before LLM invocation.
    """

    # Regex patterns for PII Anonymization
    CARD_PATTERN = r"\b(?:\d[ -]*?){13,16}\b"
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    PHONE_PATTERN = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"

    # Prompt Injection Attack Patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"disregard\s+(all\s+)?(previous|prior)\s+prompts",
        r"you\s+are\s+now\s+in\s+(developer|dan|jailbreak)\s+mode",
        r"reveal\s+your\s+(system\s+prompt|hidden\s+instructions)",
        r"bypass\s+all\s+(safety|content)\s+filters"
    ]

    @classmethod
    def sanitize_and_inspect(cls, text: str) -> Tuple[str, bool, Optional[str]]:
        """
        Sanitizes input text by masking PII and checking for security violations.
        Returns: (sanitized_text, is_safe, block_reason)
        """
        if not text:
            return text, True, None

        # 1. Inspect for Prompt Injections
        lowered = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, lowered):
                logger.warning(f"[Guardrails] Prompt injection attack detected matching: {pattern}")
                return (
                    text,
                    False,
                    "Güvenlik Politikası Uyarısı: Sistem talimatlarını aşmaya veya güvenlik protokollerini geçersiz kılmaya yönelik istekler engellenmiştir."
                )

        # 2. Anonymize PII
        sanitized = re.sub(cls.CARD_PATTERN, "[KREDİ_KARTI_MASKELEME]", text)
        sanitized = re.sub(cls.EMAIL_PATTERN, "[E-POSTA_MASKELEME]", sanitized)
        sanitized = re.sub(cls.PHONE_PATTERN, "[TELEFON_MASKELEME]", sanitized)

        return sanitized, True, None
