import time
import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.errors import ModelNotFoundError
from app.api.deps import get_auth_context, AuthContext
from app.domain.schemas import ImageGenerationRequest, ImageGenerationResponse
from app.models.entities import ModelCatalog, ModelPricing, UsageRecord
from app.providers.router import provider_router
from app.services.credit_service import CreditService

router = APIRouter()


@router.post("/images/generations", response_model=ImageGenerationResponse)
async def generate_images(
    request_body: ImageGenerationRequest,
    raw_request: Request,
    auth_ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    OpenAI-compatible Image Generation endpoint powered by AWS Bedrock (Amazon Titan Image / SDXL).
    """
    start_time = time.time()
    req_id = f"img-{uuid.uuid4().hex}"

    # Fetch Image Model
    model_name = request_body.model or "amazon.titan-image-generator-v2:0"
    stmt = select(ModelCatalog).where(
        ModelCatalog.model_id == model_name,
        ModelCatalog.is_enabled == True
    ).options(selectinload(ModelCatalog.pricing))
    res = await db.execute(stmt)
    model_entity = res.scalar_one_or_none()

    if not model_entity:
        raise ModelNotFoundError(model_name)

    # Determine Image Cost
    image_charge = model_entity.pricing.per_image_charge_usd if model_entity.pricing else Decimal("0.0500")
    total_charge = image_charge * Decimal(request_body.n or 1)

    # Pre-flight Lock & Balance Check
    await CreditService.check_and_lock_balance(
        db=db,
        user_id=auth_ctx.user.id,
        required_minimum_usd=total_charge
    )

    # Invoke Provider
    provider = provider_router.get_provider(model_entity.provider)
    result = await provider.generate_image(request_body, model_entity)

    # Deduct Credit & Create Usage Record
    duration_ms = int((time.time() - start_time) * 1000)
    await CreditService.deduct_usage(
        db=db,
        user_id=auth_ctx.user.id,
        amount_usd=total_charge,
        request_id=req_id,
        description=f"Image Gen: {model_entity.display_name} ({request_body.n} img)"
    )

    usage = UsageRecord(
        request_id=req_id,
        user_id=auth_ctx.user.id,
        api_key_id=auth_ctx.api_key.id if auth_ctx.api_key else None,
        model_id=model_entity.id,
        endpoint="/v1/images/generations",
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        provider_cost_usd=model_entity.pricing.per_image_cost_usd if model_entity.pricing else Decimal("0.0400"),
        customer_charged_usd=total_charge,
        platform_profit_usd=total_charge - (model_entity.pricing.per_image_cost_usd if model_entity.pricing else Decimal("0.0400")),
        duration_ms=duration_ms,
        status_code=200
    )
    db.add(usage)
    await db.commit()

    result.cost_usd = total_charge
    return result
