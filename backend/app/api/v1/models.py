from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.domain.schemas import ModelCatalogItem
from app.models.entities import ModelCatalog
from app.core.errors import ModelNotFoundError

router = APIRouter()


@router.get("/models", response_model=Dict[str, Any])
async def list_models(db: AsyncSession = Depends(get_db)):
    """
    OpenAI-compatible models listing.
    Returns available models, context windows, and capabilities.
    """
    stmt = (
        select(ModelCatalog)
        .where(ModelCatalog.is_enabled == True)
        .options(selectinload(ModelCatalog.pricing))
    )
    res = await db.execute(stmt)
    models = res.scalars().all()

    data = []
    for m in models:
        data.append({
            "id": m.model_id,
            "object": "model",
            "created": int(m.created_at.timestamp()),
            "owned_by": m.provider.lower(),
            "name": m.display_name,
            "context_window": m.context_window,
            "type": m.type,
            "capabilities": m.capabilities,
            "pricing": {
                "input_per_1k": float(m.pricing.customer_input_price_per_1k) if m.pricing else 0.0036,
                "output_per_1k": float(m.pricing.customer_output_price_per_1k) if m.pricing else 0.0180,
                "image_per_gen": float(m.pricing.per_image_charge_usd) if m.pricing else 0.0500,
            } if m.pricing else None
        })

    return {
        "object": "list",
        "data": data
    }


@router.get("/models/{model_id:path}")
async def get_model_details(model_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve details for a specific model."""
    stmt = (
        select(ModelCatalog)
        .where(ModelCatalog.model_id == model_id, ModelCatalog.is_enabled == True)
        .options(selectinload(ModelCatalog.pricing))
    )
    res = await db.execute(stmt)
    m = res.scalar_one_or_none()
    if not m:
        raise ModelNotFoundError(model_id)

    return {
        "id": m.model_id,
        "object": "model",
        "created": int(m.created_at.timestamp()),
        "owned_by": m.provider.lower(),
        "name": m.display_name,
        "context_window": m.context_window,
        "type": m.type,
        "capabilities": m.capabilities,
        "pricing": {
            "input_per_1k": float(m.pricing.customer_input_price_per_1k) if m.pricing else 0.0036,
            "output_per_1k": float(m.pricing.customer_output_price_per_1k) if m.pricing else 0.0180,
        } if m.pricing else None
    }
