import pytest
from decimal import Decimal
from app.services.usage_service import UsageService
from app.models.entities import ModelPricing


def test_token_cost_and_margin_calculation():
    # Example: 10,000 input tokens, 2,000 output tokens
    # Claude 3.5 Sonnet pricing:
    # Provider: $0.003 / $0.015 per 1k
    # Customer: $0.0036 / $0.018 per 1k (20% markup)
    pricing = ModelPricing(
        provider_input_price_per_1k=Decimal("0.003000"),
        provider_output_price_per_1k=Decimal("0.015000"),
        customer_input_price_per_1k=Decimal("0.003600"),
        customer_output_price_per_1k=Decimal("0.018000"),
        margin_percent=Decimal("20.00"),
        per_image_cost_usd=Decimal("0.0400"),
        per_image_charge_usd=Decimal("0.0500")
    )

    prov_cost, cust_charge, profit = UsageService.calculate_cost(
        input_tokens=10000,
        output_tokens=2000,
        pricing=pricing
    )

    # Expected:
    # prov_cost = (10 * 0.003) + (2 * 0.015) = 0.030 + 0.030 = $0.060000
    # cust_charge = (10 * 0.0036) + (2 * 0.0180) = 0.036 + 0.036 = $0.072000
    # profit = 0.072000 - 0.060000 = $0.012000 (20% margin)
    assert prov_cost == Decimal("0.060000")
    assert cust_charge == Decimal("0.072000")
    assert profit == Decimal("0.012000")
    assert cust_charge > prov_cost
