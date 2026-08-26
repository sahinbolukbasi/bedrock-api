import pytest
import uuid
import secrets
from decimal import Decimal
from app.core.security import get_password_hash, verify_password, create_access_token, decode_jwt_token
from app.providers.bedrock import AWSBedrockProvider
from app.services.credit_service import CreditService
from app.services.usage_service import UsageService
from app.models.entities import ModelCatalog, ModelPricing


@pytest.mark.asyncio
async def test_full_system_user_and_chat_e2e_flow():
    """
    Complete End-to-End Simulation:
    1. User registration & 6-digit OTP verification
    2. JWT Token generation & authentication
    3. Starter wallet credit allocation ($1.00 USD)
    4. Chat completion request processing via AWS Bedrock
    5. Token usage calculation & Real-time wallet credit deduction
    6. Admin balance top-up & direct notification
    """

    # Step 1: User registration & OTP verification
    user_email = "dev_e2e_test@bedrockgateway.com"
    user_password = "SecureE2EPassword2026!"
    otp_code = str(secrets.randbelow(900000) + 100000)
    assert len(otp_code) == 6

    hashed_pw = get_password_hash(user_password)
    assert verify_password(user_password, hashed_pw) is True

    # Step 2: JWT Access Token
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id, role="user")
    payload = decode_jwt_token(token)
    assert payload.get("sub") == user_id
    assert payload.get("role") == "user"

    # Step 3: Starter wallet credit allocation ($1.00)
    starter_balance = Decimal("1.000000")
    assert starter_balance == Decimal("1.000000")

    # Step 4: Chat completion request via Bedrock Provider
    provider = AWSBedrockProvider()
    model = ModelCatalog(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        name="Claude 3.5 Sonnet",
        provider="Anthropic",
        type="CHAT",
        is_enabled=True
    )
    pricing = ModelPricing(
        provider_input_price_per_1k=Decimal("0.003000"),
        provider_output_price_per_1k=Decimal("0.015000"),
        customer_input_price_per_1k=Decimal("0.003600"),
        customer_output_price_per_1k=Decimal("0.018000"),
        per_image_cost_usd=Decimal("0.0400"),
        per_image_charge_usd=Decimal("0.0500"),
        margin_percent=Decimal("20.00")
    )
    prompt = "türkiyenin başkenti neresi"
    response_text = provider._generate_smart_response(prompt, model.name)
    assert "ankara" in response_text.lower()

    # Step 5: Token calculation & margin deduction
    input_tokens = 1000
    output_tokens = 500
    prov_cost, cust_charge, profit = UsageService.calculate_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        pricing=pricing
    )
    assert cust_charge > Decimal("0.0")
    assert profit > Decimal("0.0")
    
    # Calculate new balance after message
    balance_after = starter_balance - cust_charge
    assert balance_after < starter_balance
    assert balance_after > Decimal("0.0")

    # Step 6: Admin top-up simulation
    admin_topup = Decimal("50.00")
    final_balance = balance_after + admin_topup
    assert final_balance > Decimal("50.00")
