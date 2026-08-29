"""
AWS Secrets Manager and Environment Vault Service.
Implements ISecretsManager port for secure dynamic secret resolution.
"""

import os
import json
import boto3
from typing import Dict, Any, Optional
from loguru import logger
from app.domain.interfaces import ISecretsManager


class AWSSecretsManagerService(ISecretsManager):
    """
    Enterprise Secrets Manager Adapter.
    Safely retrieves production secrets (API Keys, Telegram Tokens, Webhooks, DB Credentials)
    from AWS Secrets Manager or Environment variables with zero hardcoded fallback leaks.
    """

    _cached_secrets: Dict[str, Any] = {}

    @classmethod
    def get_secret(cls, secret_key: str, secret_name: Optional[str] = None, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieves a secret value dynamically:
        1. Checks local environment variable first.
        2. Checks in-memory secret cache.
        3. Fetches from AWS Secrets Manager if configured.
        4. Returns default if not found.

        Args:
            secret_key: Name of the key to resolve (e.g. "TELEGRAM_BOT_TOKEN")
            secret_name: AWS Secret ID/ARN (defaults to AWS_SECRET_NAME or "bedrock-gateway-secrets-prod")
            default: Fallback default value if key is not configured

        Returns:
            Optional[str]: The secret string or default
        """
        # 1. Check local environment variable first
        env_val = os.getenv(secret_key)
        if env_val is not None and env_val.strip() != "":
            return env_val.strip()

        # 2. Check in-memory cache
        if secret_key in cls._cached_secrets:
            return cls._cached_secrets[secret_key]

        # 3. Fetch from AWS Secrets Manager
        target_secret_name = secret_name or os.getenv("AWS_SECRET_NAME", "bedrock-gateway-secrets-prod")
        aws_region = os.getenv("AWS_REGION", "us-east-1")

        try:
            client = boto3.client("secretsmanager", region_name=aws_region)
            response = client.get_secret_value(SecretId=target_secret_name)
            if "SecretString" in response:
                secret_dict = json.loads(response["SecretString"])
                cls._cached_secrets.update(secret_dict)
                return cls._cached_secrets.get(secret_key, default)
        except Exception as e:
            logger.debug(f"[SecretsManager] AWS Secrets fetch note ({target_secret_name}): {e}")

        return default

    @classmethod
    def set_cached_secret(cls, key: str, value: Any) -> None:
        """Utility for testing and runtime secret overrides."""
        cls._cached_secrets[key] = value

    @classmethod
    def clear_cache(cls) -> None:
        """Clears all cached secrets."""
        cls._cached_secrets.clear()


# Global Singleton Instance
secrets_manager = AWSSecretsManagerService()
