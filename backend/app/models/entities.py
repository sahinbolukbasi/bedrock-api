import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, String, Boolean, DateTime, Numeric, Integer, ForeignKey, Text, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="user", nullable=False)  # "user" | "admin"
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    credit_purchases = relationship("CreditPurchase", back_populates="user")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    prefix = Column(String(16), nullable=False, index=True)  # e.g., "sk-live-a1b2..."
    hashed_secret = Column(String(128), unique=True, nullable=False, index=True)  # SHA-256 hash of full token
    rate_limit_rpm = Column(Integer, default=120, nullable=False)
    spending_limit_usd = Column(Numeric(14, 4), nullable=True)
    spending_used_usd = Column(Numeric(14, 4), default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="api_keys")
    usage_records = relationship("UsageRecord", back_populates="api_key")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance_usd = Column(Numeric(14, 6), default=Decimal("0.000000"), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    version = Column(Integer, default=1, nullable=False)  # Optimistic concurrency control
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="wallet")
    transactions = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan", order_by="desc(WalletTransaction.created_at)")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    amount_usd = Column(Numeric(14, 6), nullable=False)  # Positive for additions, negative for deductions
    type = Column(String(50), nullable=False)  # "PURCHASE", "USAGE_DEDUCTION", "REFUND", "BONUS"
    reference_id = Column(String(128), nullable=True, index=True)  # e.g., Stripe Session ID or Request ID
    balance_after = Column(Numeric(14, 6), nullable=False)
    idempotency_key = Column(String(128), unique=True, nullable=True, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    wallet = relationship("Wallet", back_populates="transactions")


class CreditPurchase(Base):
    __tablename__ = "credit_purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    stripe_session_id = Column(String(128), unique=True, nullable=False, index=True)
    stripe_payment_intent_id = Column(String(128), nullable=True, index=True)
    amount_usd = Column(Numeric(10, 2), nullable=False)
    credits_added = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # "PENDING", "COMPLETED", "FAILED", "REFUNDED"
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="credit_purchases")


class ModelCatalog(Base):
    __tablename__ = "models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(String(128), unique=True, nullable=False, index=True)  # Bedrock ID: "anthropic.claude-3-5-sonnet-20241022-v2:0"
    provider = Column(String(50), default="BEDROCK", nullable=False)
    name = Column(String(128), nullable=False)
    display_name = Column(String(128), nullable=False)
    type = Column(String(50), default="CHAT", nullable=False)  # "CHAT", "TEXT", "EMBEDDING", "IMAGE", "VIDEO"
    context_window = Column(Integer, default=200000, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    region = Column(String(50), default="us-east-1", nullable=False)
    capabilities = Column(JSON, default=dict, nullable=False)  # {"vision": true, "tools": true, "streaming": true}
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    pricing = relationship("ModelPricing", back_populates="model", uselist=False, cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="model")


class ModelPricing(Base):
    __tablename__ = "model_pricing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), unique=True, nullable=False)
    # Price per 1,000 tokens (or per image generation)
    provider_input_price_per_1k = Column(Numeric(10, 6), default=Decimal("0.003000"), nullable=False)
    provider_output_price_per_1k = Column(Numeric(10, 6), default=Decimal("0.015000"), nullable=False)
    customer_input_price_per_1k = Column(Numeric(10, 6), default=Decimal("0.003600"), nullable=False)
    customer_output_price_per_1k = Column(Numeric(10, 6), default=Decimal("0.018000"), nullable=False)
    margin_percent = Column(Numeric(5, 2), default=Decimal("20.00"), nullable=False)  # 20% margin
    per_image_cost_usd = Column(Numeric(10, 4), default=Decimal("0.0400"), nullable=False)
    per_image_charge_usd = Column(Numeric(10, 4), default=Decimal("0.0500"), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    model = relationship("ModelCatalog", back_populates="pricing")


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True, index=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="RESTRICT"), nullable=False, index=True)
    endpoint = Column(String(128), default="/v1/chat/completions", nullable=False)
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    provider_cost_usd = Column(Numeric(14, 6), default=Decimal("0.000000"), nullable=False)
    customer_charged_usd = Column(Numeric(14, 6), default=Decimal("0.000000"), nullable=False)
    platform_profit_usd = Column(Numeric(14, 6), default=Decimal("0.000000"), nullable=False)
    duration_ms = Column(Integer, default=0, nullable=False)
    status_code = Column(Integer, default=200, nullable=False)
    error_code = Column(String(64), nullable=True)
    ip_hash = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="usage_records")
    api_key = relationship("ApiKey", back_populates="usage_records")
    model = relationship("ModelCatalog", back_populates="usage_records")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Chat", nullable=False)
    model_id = Column(String(128), nullable=False)
    system_prompt = Column(Text, nullable=True)
    temperature = Column(Numeric(3, 2), default=Decimal("0.70"), nullable=False)
    max_tokens = Column(Integer, default=4096, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    tokens = Column(Integer, default=0, nullable=False)
    cost_usd = Column(Numeric(10, 6), default=Decimal("0.000000"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)  # "IMAGE", "VIDEO"
    model_id = Column(String(128), nullable=False)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    parameters = Column(JSON, default=dict, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # "PENDING", "PROCESSING", "COMPLETED", "FAILED"
    s3_key = Column(String(512), nullable=True)
    cost_usd = Column(Numeric(10, 4), default=Decimal("0.0000"), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(128), nullable=False)  # "USER_SUSPENDED", "PRICE_CHANGED", "KEY_REVOKED", "ADMIN_LOGIN"
    resource_type = Column(String(64), nullable=False)  # "USER", "MODEL", "API_KEY", "WALLET"
    resource_id = Column(String(128), nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")


class CustomAgent(Base):
    __tablename__ = "custom_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    model_id = Column(String(128), default="anthropic.claude-3-5-sonnet-20241022-v2:0", nullable=False)
    system_prompt = Column(Text, nullable=False)
    tools_config = Column(JSON, default=dict, nullable=False)  # {"email_notifications": true, "telegram_webhook": "...", "data_tracking": true}
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
