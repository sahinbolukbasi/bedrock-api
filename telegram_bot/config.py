import os
import json
from typing import Optional
from loguru import logger

class TelegramConfig:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "REDACTED_TELEGRAM_BOT_TOKEN")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com:8000")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    SECRET_ID: str = os.getenv("SECRET_ID", "bedrock-gateway-secrets-prod")
    MAX_PROMPT_LENGTH: int = 4000
    RATE_LIMIT_PER_MINUTE: int = 30

    @classmethod
    def load_from_aws_secrets(cls):
        """
        Dynamically fetches production secrets from AWS Secrets Manager if available.
        Ensures credentials are never hardcoded or exposed in logs.
        """
        try:
            import boto3
            client = boto3.client("secretsmanager", region_name=cls.AWS_REGION)
            response = client.get_secret_value(SecretId=cls.SECRET_ID)
            if "SecretString" in response:
                secrets = json.loads(response["SecretString"])
                if "TELEGRAM_BOT_TOKEN" in secrets:
                    cls.TELEGRAM_BOT_TOKEN = secrets["TELEGRAM_BOT_TOKEN"]
                    logger.info("[TelegramBot] Successfully loaded Telegram Token from AWS Secrets Manager.")
        except Exception as e:
            logger.warning(f"[TelegramBot] Running with default environment config: {e}")

config = TelegramConfig()
