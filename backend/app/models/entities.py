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
    phone_number = Column(String(50), nullable=True)
    avatar_url = Column(String(1024), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="user", nullable=False)  # "user" | "admin"
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(64), nullable=True)
    telegram_chat_id = Column(String(64), nullable=True, index=True)
    telegram_username = Column(String(128), nullable=True)
    telegram_pairing_code = Column(String(32), nullable=True, index=True)
    telegram_active_agent_id = Column(UUID(as_uuid=True), nullable=True)
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
    scheduled_tasks = relationship("ScheduledTask", back_populates="user", cascade="all, delete-orphan")


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
    summary_context = Column(Text, default="", nullable=False)  # Compressed Layer-1 rolling memory
    scratchpad = Column(Text, default="", nullable=False)  # Working Layer-3 memory
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
    icon = Column(String(64), default="🤖", nullable=False)
    agent_type = Column(String(64), default="custom", nullable=False)  # "news", "finance", "security", "custom"
    goal_definition = Column(Text, default="", nullable=False)  # Success metrics & goal
    autonomy_level = Column(String(32), default="AUTONOMOUS", nullable=False)  # "AUTONOMOUS", "CONFIRMATION_REQUIRED", "ADVISORY"
    description = Column(Text, nullable=True)
    model_id = Column(String(128), default="amazon.nova-micro-v1:0", nullable=False)
    system_prompt = Column(Text, nullable=False)
    schedule_cron = Column(String(64), nullable=True)  # e.g., "0 * * * *" (hourly), "0 9 * * *" (daily)
    schedule_enabled = Column(Boolean, default=False, nullable=False)
    learned_memory_cache = Column(Text, default="", nullable=False)  # Layer-2 Long-term facts & preferences
    memory_settings = Column(JSON, default=dict, nullable=False)  # {"compression": true, "max_context": 4000}
    tools_config = Column(JSON, default=dict, nullable=False)  # {"web_search": true, "telegram": true, "math": true}
    is_active = Column(Boolean, default=True, nullable=False)
    total_runs = Column(Integer, default=0, nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


    execution_logs = relationship("AgentExecutionLog", back_populates="agent", cascade="all, delete-orphan")


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("custom_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_type = Column(String(50), default="MANUAL", nullable=False)  # "MANUAL", "TELEGRAM", "SCHEDULE_CRON", "WEBHOOK"
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=False)
    learned_insight = Column(Text, nullable=True)
    status = Column(String(50), default="COMPLETED", nullable=False)
    cost_usd = Column(Numeric(10, 6), default=Decimal("0.002000"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    agent = relationship("CustomAgent", back_populates="execution_logs")


class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(String(50), nullable=False)  # "REMINDER", "WEB_SEARCH_TRACKER", "AGENT_CRON", "IMAGE_GEN"
    title = Column(String(255), nullable=False)
    payload = Column(JSON, default=dict, nullable=False)  # {"prompt": "...", "search_query": "...", "chat_id": "..."}
    schedule_type = Column(String(50), default="ONCE", nullable=False)  # "ONCE", "INTERVAL", "CRON"
    interval_seconds = Column(Integer, nullable=True)  # e.g., 3600 for hourly
    cron_expression = Column(String(64), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False, index=True)  # "ACTIVE", "COMPLETED", "CANCELLED", "PAUSED"
    run_count = Column(Integer, default=0, nullable=False)
    last_result_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="scheduled_tasks")
