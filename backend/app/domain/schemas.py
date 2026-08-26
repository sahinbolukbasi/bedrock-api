from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, EmailStr, Field
import uuid


# ==========================================
# Authentication & User Schemas
# ==========================================
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: str
    role: str
    mfa_required: bool = False


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    role: str
    mfa_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class MFAVerifyRequest(BaseModel):
    code: str


# ==========================================
# API Key Schemas
# ==========================================
class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    rate_limit_rpm: int = Field(default=120, ge=1, le=10000)
    spending_limit_usd: Optional[Decimal] = Field(default=None, ge=0)
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)


class ApiKeyCreatedResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    api_key: str  # ONLY RETURNED ONCE UPON CREATION!
    rate_limit_rpm: int
    spending_limit_usd: Optional[Decimal]
    created_at: datetime


class ApiKeyListItem(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    rate_limit_rpm: int
    spending_limit_usd: Optional[Decimal]
    spending_used_usd: Decimal
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Wallet & Billing Schemas
# ==========================================
class WalletResponse(BaseModel):
    balance_usd: Decimal
    currency: str = "USD"
    updated_at: datetime

    class Config:
        from_attributes = True


class WalletTransactionItem(BaseModel):
    id: uuid.UUID
    amount_usd: Decimal
    type: str
    balance_after: Decimal
    reference_id: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CreditPackageItem(BaseModel):
    package_id: str
    name: str
    amount_usd: Decimal
    bonus_usd: Decimal
    total_credits: Decimal


class CheckoutSessionRequest(BaseModel):
    package_id: str  # e.g., "tier_10", "tier_25", "tier_50", "tier_100"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


# ==========================================
# Model Catalog Schemas
# ==========================================
class ModelPricingSchema(BaseModel):
    provider_input_price_per_1k: Decimal
    provider_output_price_per_1k: Decimal
    customer_input_price_per_1k: Decimal
    customer_output_price_per_1k: Decimal
    margin_percent: Decimal
    per_image_charge_usd: Decimal

    class Config:
        from_attributes = True


class ModelCatalogItem(BaseModel):
    id: uuid.UUID
    model_id: str
    provider: str
    name: str
    display_name: str
    type: str
    context_window: int
    is_enabled: bool
    capabilities: Dict[str, Any]
    pricing: Optional[ModelPricingSchema]

    class Config:
        from_attributes = True


# ==========================================
# OpenAI-Compatible Chat API Schemas
# ==========================================
class ChatMessageContentPart(BaseModel):
    type: str  # "text" | "image_url"
    text: Optional[str] = None
    image_url: Optional[Dict[str, str]] = None


class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: Union[str, List[ChatMessageContentPart]]
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = Field(default=4096, ge=1)
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None


class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: Optional[Decimal] = None


class ChatChoiceMessage(BaseModel):
    role: str = "assistant"
    content: Optional[str] = None


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatChoiceMessage
    finish_reason: Optional[str] = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: UsageInfo
    system_fingerprint: Optional[str] = "fp_bedrock_gateway"


class ChatChunkDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class ChatChunkChoice(BaseModel):
    index: int = 0
    delta: ChatChunkDelta
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatChunkChoice]


# ==========================================
# Image Generation Schemas
# ==========================================
class ImageGenerationRequest(BaseModel):
    prompt: str
    model: Optional[str] = "amazon.titan-image-generator-v2:0"
    n: Optional[int] = Field(default=1, ge=1, le=4)
    size: Optional[str] = "1024x1024"  # "512x512", "1024x1024"
    negative_prompt: Optional[str] = None
    aspect_ratio: Optional[str] = "1:1"  # "1:1", "16:9", "9:16", "4:3", "3:4"


class ImageItem(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None


class ImageGenerationResponse(BaseModel):
    created: int
    data: List[ImageItem]
    cost_usd: Decimal


# ==========================================
# Admin & Analytics Schemas
# ==========================================
class AdminOverviewStats(BaseModel):
    total_users: int
    active_api_keys: int
    total_revenue_usd: Decimal
    total_provider_cost_usd: Decimal
    platform_net_profit_usd: Decimal
    total_requests: int
    total_tokens_served: int
    avg_latency_ms: float


class UsageAnalyticsItem(BaseModel):
    date: str
    requests: int
    tokens: int
    cost_usd: Decimal
    revenue_usd: Decimal
    profit_usd: Decimal
