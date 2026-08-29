"""
Global Configuration & Dynamic Secrets Resolver for AWS Bedrock AI Gateway.
Centralizes all environment parameters with dynamic Key Vault integration.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from app.core.secrets_manager import AWSSecretsManagerService


class Settings(BaseSettings):
    """
    Application Settings schema.
    Dynamic values are loaded from Environment variables and AWS Secrets Manager.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

    PROJECT_NAME: str = "Bedrock AI Gateway"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    ENVIRONMENT: str = Field(default="production", description="Environment: production, staging, development, test")

    # Security & Auth JWT
    SECRET_KEY: str = Field(
        default_factory=lambda: AWSSecretsManagerService.get_secret(
            "SECRET_KEY", 
            default="bedrock-gateway-jwt-secure-signing-key-32-chars-minimum"
        )
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = Field(
        default_factory=lambda: AWSSecretsManagerService.get_secret(
            "DATABASE_URL",
            default="sqlite+aiosqlite:///./bedrock_local.db"
        )
    )

    # Redis Cache
    REDIS_URL: str = Field(
        default_factory=lambda: AWSSecretsManagerService.get_secret(
            "REDIS_URL",
            default="redis://127.0.0.1:6379/0"
        )
    )

    # AWS Settings (IAM roles used on ECS Fargate)
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "bedrock-gateway-artifacts-prod"
    S3_PRESIGNED_EXPIRY_SECONDS: int = 3600

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = Field(
        default_factory=lambda: AWSSecretsManagerService.get_secret("STRIPE_SECRET_KEY")
    )
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(
        default_factory=lambda: AWSSecretsManagerService.get_secret("STRIPE_WEBHOOK_SECRET")
    )

    # CORS Allowed Origins
    CORS_ORIGINS: List[str] = [
        "http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com",
        "https://app.bedrockgateway.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    # Rate Limiting & Abuse Protection
    DEFAULT_RATE_LIMIT_RPM: int = 120
    DEFAULT_MAX_CONCURRENT_REQUESTS: int = 10
    MINIMUM_WALLET_BALANCE_FOR_REQUEST_USD: float = 0.001

    # Admin Identity
    ADMIN_EMAIL: str = Field(
        default_factory=lambda: AWSSecretsManagerService.get_secret("ADMIN_EMAIL", default="admin@bedrockgateway.com")
    )
    ADMIN_PASSWORD: Optional[str] = Field(
        default_factory=lambda: AWSSecretsManagerService.get_secret("ADMIN_PASSWORD")
    )

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(
        default_factory=lambda: AWSSecretsManagerService.get_secret("TELEGRAM_BOT_TOKEN")
    )
    TELEGRAM_BOT_USERNAME: str = Field(
        default_factory=lambda: AWSSecretsManagerService.get_secret("TELEGRAM_BOT_USERNAME", default="BedrocksAiBot")
    )

    # Prometheus Metrics Security
    METRICS_SCRAPE_TOKEN: str = Field(
        default_factory=lambda: AWSSecretsManagerService.get_secret(
            "METRICS_SCRAPE_TOKEN", 
            default="bedrock-metrics-secret-token-key-2026"
        ),
        description="Bearer token required to scrape /metrics endpoint"
    )

    # Email & SMTP Settings
    EMAIL_SENDER: str = Field(
        default_factory=lambda: AWSSecretsManagerService.get_secret("EMAIL_SENDER", default="noreply@bedrockgateway.com"),
        description="Default sender address for system emails"
    )
    SMTP_HOST: Optional[str] = Field(default_factory=lambda: AWSSecretsManagerService.get_secret("SMTP_HOST"))
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default_factory=lambda: AWSSecretsManagerService.get_secret("SMTP_USER"))
    SMTP_PASS: Optional[str] = Field(default_factory=lambda: AWSSecretsManagerService.get_secret("SMTP_PASS"))
    SMTP_USE_TLS: bool = True


# Instantiate Global Settings
settings = Settings()
