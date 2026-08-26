import uuid
from decimal import Decimal
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_active_admin
from app.domain.schemas import AdminOverviewStats, ModelCatalogItem
from app.models.entities import User, ApiKey, UsageRecord, ModelCatalog, ModelPricing, AuditLog, Wallet

router = APIRouter()


@router.get("/overview", response_model=AdminOverviewStats)
async def get_admin_overview(
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    # Total users
    users_count = await db.scalar(select(func.count(User.id)))
    # Active keys
    keys_count = await db.scalar(select(func.count(ApiKey.id)).where(ApiKey.is_active == True))
    
    # Financials and token aggregates
    usage_stats = await db.execute(
        select(
            func.coalesce(func.sum(UsageRecord.customer_charged_usd), Decimal("0.0")),
            func.coalesce(func.sum(UsageRecord.provider_cost_usd), Decimal("0.0")),
            func.coalesce(func.sum(UsageRecord.platform_profit_usd), Decimal("0.0")),
            func.count(UsageRecord.id),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0),
            func.coalesce(func.avg(UsageRecord.duration_ms), 0.0)
        )
    )
    rev, cost, profit, reqs, tokens, avg_lat = usage_stats.first()

    return AdminOverviewStats(
        total_users=users_count or 0,
        active_api_keys=keys_count or 0,
        total_revenue_usd=rev,
        total_provider_cost_usd=cost,
        platform_net_profit_usd=profit,
        total_requests=reqs or 0,
        total_tokens_served=tokens or 0,
        avg_latency_ms=float(avg_lat)
    )


@router.get("/users")
async def list_admin_users(
    limit: int = 50,
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(User)
        .options(selectinload(User.wallet))
        .order_by(User.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    users = res.scalars().all()
    return [{
        "id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role,
        "is_active": u.is_active,
        "is_verified": u.is_verified,
        "balance_usd": float(u.wallet.balance_usd) if u.wallet else 0.0,
        "created_at": u.created_at
    } for u in users]


@router.post("/users/{user_id}/status")
async def update_user_status(
    user_id: uuid.UUID,
    is_active: bool,
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = is_active
    audit = AuditLog(
        user_id=admin_user.id,
        action="USER_STATUS_UPDATED",
        resource_type="USER",
        resource_id=str(user.id),
        details={"new_status": is_active}
    )
    db.add(audit)
    await db.commit()
    return {"message": f"User status set to {'active' if is_active else 'suspended'}"}


@router.post("/models/{model_id}/pricing")
async def update_model_pricing(
    model_id: uuid.UUID,
    customer_input_price_per_1k: Decimal,
    customer_output_price_per_1k: Decimal,
    margin_percent: Decimal,
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ModelPricing).where(ModelPricing.model_id == model_id)
    res = await db.execute(stmt)
    pricing = res.scalar_one_or_none()
    if not pricing:
        raise HTTPException(status_code=404, detail="Model pricing not found")

    pricing.customer_input_price_per_1k = customer_input_price_per_1k
    pricing.customer_output_price_per_1k = customer_output_price_per_1k
    pricing.margin_percent = margin_percent

    audit = AuditLog(
        user_id=admin_user.id,
        action="MODEL_PRICING_UPDATED",
        resource_type="MODEL_PRICING",
        resource_id=str(model_id),
        details={"margin": float(margin_percent)}
    )
    db.add(audit)
    await db.commit()
    return {"message": "Model pricing updated successfully"}


@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = 100,
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()
