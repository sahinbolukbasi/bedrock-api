import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, AnyHttpUrl, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bedrock AI Gateway"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # Security & Auth
    SECRET_KEY: str = Field(default="super-secret-key-change-in-production-min-32-chars", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Database (PostgreSQL)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/bedrock_gateway",
        env="DATABASE_URL"
    )

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # AWS Settings (In production on ECS/EKS, IAM roles are used automatically without static keys)
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME: str = Field(default="bedrock-gateway-artifacts-prod", env="S3_BUCKET_NAME")
    S3_PRESIGNED_EXPIRY_SECONDS: int = 3600

    # Stripe
    STRIPE_SECRET_KEY: str = Field(default="sk_test_placeholder", env="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(default="whsec_placeholder", env="STRIPE_WEBHOOK_SECRET")

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "https://app.bedrockgateway.com"]

    # Rate Limiting & Abuse Protection
    DEFAULT_RATE_LIMIT_RPM: int = 120  # requests per minute
    DEFAULT_MAX_CONCURRENT_REQUESTS: int = 10
    MINIMUM_WALLET_BALANCE_FOR_REQUEST_USD: float = 0.001

    # Admin seed
    ADMIN_EMAIL: str = Field(default="admin@bedrockgateway.com", env="ADMIN_EMAIL")
    ADMIN_PASSWORD: str = Field(default="AdminPassword123!", env="ADMIN_PASSWORD")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
