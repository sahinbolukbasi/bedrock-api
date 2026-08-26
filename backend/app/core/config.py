import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

    PROJECT_NAME: str = "Bedrock AI Gateway"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    ENVIRONMENT: str = "production"

    # Security & Auth
    SECRET_KEY: str = "super-secure-production-jwt-key-32-chars-minimum"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Database (Amazon RDS PostgreSQL 16)
    DATABASE_URL: str = "postgresql+asyncpg://bedrockadmin:BedrockSecurePassword2026!@bedrock-gateway-db.cobqqmqcs7xh.us-east-1.rds.amazonaws.com:5432/bedrock_gateway"

    # Redis (Amazon ElastiCache Redis 7)
    REDIS_URL: str = "redis://bedrock-gateway-redis.hmoplf.0001.use1.cache.amazonaws.com:6379/0"

    # AWS Settings (IAM roles used on ECS Fargate)
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "bedrock-gateway-artifacts-prod"
    S3_PRESIGNED_EXPIRY_SECONDS: int = 3600

    # Stripe
    STRIPE_SECRET_KEY: str = "sk_test_placeholder"
    STRIPE_WEBHOOK_SECRET: str = "whsec_placeholder"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com",
        "https://app.bedrockgateway.com",
        "*"
    ]

    # Rate Limiting & Abuse Protection
    DEFAULT_RATE_LIMIT_RPM: int = 120
    DEFAULT_MAX_CONCURRENT_REQUESTS: int = 10
    MINIMUM_WALLET_BALANCE_FOR_REQUEST_USD: float = 0.001

    # Admin seed
    ADMIN_EMAIL: str = "admin@bedrockgateway.com"
    ADMIN_PASSWORD: str = "AdminPassword123!"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = "REDACTED_TELEGRAM_BOT_TOKEN"


settings = Settings()
