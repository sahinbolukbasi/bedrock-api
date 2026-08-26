import uuid
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import ModelCatalog, ModelPricing, UsageRecord, ApiKey
from app.services.credit_service import CreditService
from loguru import logger


class UsageService:
    @staticmethod
    def calculate_cost(
        input_tokens: int,
        output_tokens: int,
        pricing: Optional[ModelPricing]
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculates (provider_cost, customer_charge, platform_profit)
        """
        if not pricing:
            # Default fallback pricing ($0.003 / $0.015 per 1k)
            prov_in = Decimal("0.003000")
            prov_out = Decimal("0.015000")
            cust_in = Decimal("0.003600")
            cust_out = Decimal("0.018000")
        else:
            prov_in = pricing.provider_input_price_per_1k
            prov_out = pricing.provider_output_price_per_1k
            cust_in = pricing.customer_input_price_per_1k
            cust_out = pricing.customer_output_price_per_1k

        in_k = Decimal(input_tokens) / Decimal(1000)
        out_k = Decimal(output_tokens) / Decimal(1000)

        provider_cost = (in_k * prov_in) + (out_k * prov_out)
        customer_charge = (in_k * cust_in) + (out_k * cust_out)

        # Minimum charge floor ($0.000001)
        if customer_charge <= 0 and (input_tokens > 0 or output_tokens > 0):
            customer_charge = Decimal("0.000001")

        platform_profit = customer_charge - provider_cost
        return (
            provider_cost.quantize(Decimal("0.000001")),
            customer_charge.quantize(Decimal("0.000001")),
            platform_profit.quantize(Decimal("0.000001"))
        )

    @staticmethod
    async def record_and_charge_usage(
        db: AsyncSession,
        request_id: str,
        user_id: uuid.UUID,
        model_entity: ModelCatalog,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        api_key_id: Optional[uuid.UUID] = None,
        endpoint: str = "/v1/chat/completions",
        status_code: int = 200,
        ip_hash: Optional[str] = None
    ) -> UsageRecord:
        """
        Records the token metrics, calculates provider & customer pricing with margins,
        and deducts the amount atomically from user's wallet.
        """
        # Load pricing
        pricing_stmt = select(ModelPricing).where(ModelPricing.model_id == model_entity.id)
        pricing_res = await db.execute(pricing_stmt)
        pricing = pricing_res.scalar_one_or_none()

        provider_cost, customer_charge, profit = UsageService.calculate_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            pricing=pricing
        )

        # Create usage record
        usage = UsageRecord(
            request_id=request_id,
            user_id=user_id,
            api_key_id=api_key_id,
            model_id=model_entity.id,
            endpoint=endpoint,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            provider_cost_usd=provider_cost,
            customer_charged_usd=customer_charge,
            platform_profit_usd=profit,
            duration_ms=duration_ms,
            status_code=status_code,
            ip_hash=ip_hash
        )
        db.add(usage)

        # Update API key spending tracked
        if api_key_id:
            api_key_stmt = select(ApiKey).where(ApiKey.id == api_key_id)
            api_key_res = await db.execute(api_key_stmt)
            api_key = api_key_res.scalar_one_or_none()
            if api_key:
                api_key.spending_used_usd = (api_key.spending_used_usd or Decimal("0")) + customer_charge

        # Atomic deduction from wallet
        if customer_charge > 0:
            await CreditService.deduct_usage(
                db=db,
                user_id=user_id,
                amount_usd=customer_charge,
                request_id=request_id,
                description=f"Usage for {model_entity.display_name} ({input_tokens}+{output_tokens} tok)"
            )
        else:
            await db.commit()

        await db.refresh(usage)
        return usage
