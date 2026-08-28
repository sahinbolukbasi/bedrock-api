import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import generate_api_key
from app.core.errors import GatewayAPIException
from app.api.deps import get_current_user
from app.domain.schemas import ApiKeyCreateRequest, ApiKeyCreatedResponse, ApiKeyListItem
from app.models.entities import User, ApiKey, AuditLog

router = APIRouter()


@router.get("", response_model=List[ApiKeyListItem])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ApiKey)
        .where(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    body: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    full_key, prefix, hashed_secret = generate_api_key(prefix_label="live")
    
    expires_at = None
    if body.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)

    api_key_obj = ApiKey(
        user_id=current_user.id,
        name=body.name,
        prefix=prefix,
        hashed_secret=hashed_secret,
        rate_limit_rpm=body.rate_limit_rpm,
        spending_limit_usd=body.spending_limit_usd,
        expires_at=expires_at
    )
    db.add(api_key_obj)

    # Add audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="API_KEY_CREATED",
        resource_type="API_KEY",
        resource_id=str(api_key_obj.id),
        details={"name": body.name, "prefix": prefix}
    )
    db.add(audit)

    await db.commit()
    await db.refresh(api_key_obj)

    return ApiKeyCreatedResponse(
        id=api_key_obj.id,
        name=api_key_obj.name,
        prefix=api_key_obj.prefix,
        api_key=full_key,  # Returned only on creation
        rate_limit_rpm=api_key_obj.rate_limit_rpm,
        spending_limit_usd=api_key_obj.spending_limit_usd,
        created_at=api_key_obj.created_at
    )


from app.domain.schemas import ApiKeyCreateRequest, ApiKeyCreatedResponse, ApiKeyListItem, ApiKeyUpdateRequest
from app.models.entities import User, ApiKey, AuditLog, UsageRecord, ModelCatalog


@router.patch("/{key_id}", response_model=ApiKeyListItem)
@router.put("/{key_id}", response_model=ApiKeyListItem)
async def update_api_key(
    key_id: uuid.UUID,
    body: ApiKeyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    res = await db.execute(stmt)
    key = res.scalar_one_or_none()
    if not key:
        raise GatewayAPIException(status_code=404, message="API Key not found.")

    if body.name is not None:
        key.name = body.name
    if body.rate_limit_rpm is not None:
        key.rate_limit_rpm = body.rate_limit_rpm
    if body.spending_limit_usd is not None:
        key.spending_limit_usd = body.spending_limit_usd
    if body.is_active is not None:
        key.is_active = body.is_active

    audit = AuditLog(
        user_id=current_user.id,
        action="API_KEY_UPDATED",
        resource_type="API_KEY",
        resource_id=str(key.id),
        details={"name": key.name, "spending_limit_usd": str(key.spending_limit_usd)}
    )
    db.add(audit)
    await db.commit()
    await db.refresh(key)
    return key


@router.get("/{key_id}/logs")
async def get_api_key_logs(
    key_id: uuid.UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    res = await db.execute(stmt)
    key = res.scalar_one_or_none()
    if not key:
        raise GatewayAPIException(status_code=404, message="API Key not found.")

    log_stmt = (
        select(UsageRecord, ModelCatalog.display_name)
        .outerjoin(ModelCatalog, UsageRecord.model_id == ModelCatalog.id)
        .where(UsageRecord.api_key_id == key_id)
        .order_by(UsageRecord.created_at.desc())
        .limit(limit)
    )
    log_res = await db.execute(log_stmt)
    rows = log_res.all()

    return [{
        "request_id": row[0].request_id,
        "model_name": row[1] or row[0].endpoint,
        "endpoint": row[0].endpoint,
        "input_tokens": row[0].input_tokens,
        "output_tokens": row[0].output_tokens,
        "total_tokens": row[0].total_tokens,
        "customer_charged_usd": float(row[0].customer_charged_usd),
        "duration_ms": row[0].duration_ms,
        "status_code": row[0].status_code,
        "created_at": row[0].created_at
    } for row in rows]


@router.post("/{key_id}/revoke")
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    res = await db.execute(stmt)
    key = res.scalar_one_or_none()
    if not key:
        raise GatewayAPIException(status_code=404, message="API Key not found.")

    key.is_active = False
    audit = AuditLog(
        user_id=current_user.id,
        action="API_KEY_REVOKED",
        resource_type="API_KEY",
        resource_id=str(key.id),
        details={"prefix": key.prefix}
    )
    db.add(audit)
    await db.commit()
    return {"message": "API key successfully revoked."}


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    res = await db.execute(stmt)
    key = res.scalar_one_or_none()
    if not key:
        raise GatewayAPIException(status_code=404, message="API Key not found.")

    await db.delete(key)
    await db.commit()
    return {"message": "API key deleted permanently."}
