import os
import json
import boto3
from typing import Dict, Any, Optional
from loguru import logger


class AWSSecretsManagerService:
    """
    Enterprise AWS Secrets Manager Client.
    Safely retrieves production secrets (API Keys, Telegram Tokens, Webhooks)
    without keeping any hardcoded tokens in source code.
    """

    _cached_secrets: Dict[str, Any] = {}

    @classmethod
    def get_secret(cls, secret_key: str, secret_name: Optional[str] = None, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieves a secret value by key.
        1. Checks in-memory cache.
        2. Checks environment variables.
        3. Fetches from AWS Secrets Manager if configured.
        """
        # 1. Check local environment variable first
        env_val = os.getenv(secret_key)
        if env_val:
            return env_val

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
            # Fallback when outside AWS or running in local dev mode
            logger.debug(f"[SecretsManager] AWS Secrets fetch note ({target_secret_name}): {e}")

        return default
