from decimal import Decimal
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.entities import User, UsageRecord, ModelCatalog

router = APIRouter()


@router.get("/summary")
async def get_user_usage_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stats = await db.execute(
        select(
            func.coalesce(func.sum(UsageRecord.customer_charged_usd), Decimal("0.0")),
            func.count(UsageRecord.id),
            func.coalesce(func.sum(UsageRecord.input_tokens), 0),
            func.coalesce(func.sum(UsageRecord.output_tokens), 0),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0),
        ).where(UsageRecord.user_id == current_user.id)
    )
    total_cost, total_requests, in_tok, out_tok, total_tok = stats.first()

    return {
        "total_spent_usd": float(total_cost),
        "total_requests": total_requests,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "total_tokens": total_tok
    }


@router.get("/recent")
async def get_recent_activity(
    limit: int = 25,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(UsageRecord, ModelCatalog.display_name)
        .join(ModelCatalog, UsageRecord.model_id == ModelCatalog.id)
        .where(UsageRecord.user_id == current_user.id)
        .order_by(UsageRecord.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    rows = res.all()

    return [{
        "request_id": row[0].request_id,
        "model_name": row[1],
        "endpoint": row[0].endpoint,
        "total_tokens": row[0].total_tokens,
        "customer_charged_usd": float(row[0].customer_charged_usd),
        "duration_ms": row[0].duration_ms,
        "status_code": row[0].status_code,
        "created_at": row[0].created_at
    } for row in rows]
