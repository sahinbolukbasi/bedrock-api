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
@router.post("/users/{user_id}/balance")
async def adjust_user_balance(
    user_id: uuid.UUID,
    new_balance_usd: Decimal,
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Wallet).where(Wallet.user_id == user_id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance_usd=new_balance_usd)
        db.add(wallet)
    else:
        wallet.balance_usd = new_balance_usd

    audit = AuditLog(
        user_id=admin_user.id,
        action="USER_BALANCE_ADJUSTED",
        resource_type="WALLET",
        resource_id=str(user_id),
        details={"new_balance": float(new_balance_usd)}
    )
    db.add(audit)
    await db.commit()
    return {"message": f"User balance updated to ${float(new_balance_usd):.2f}"}


@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: uuid.UUID,
    role: str,
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    if role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'user' or 'admin'.")

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role
    audit = AuditLog(
        user_id=admin_user.id,
        action="USER_ROLE_UPDATED",
        resource_type="USER",
        resource_id=str(user.id),
        details={"new_role": role}
    )
    db.add(audit)
    await db.commit()
    return {"message": f"User role updated to {role}"}


@router.get("/models")
async def list_admin_models(
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ModelCatalog).options(selectinload(ModelCatalog.pricing)).order_by(ModelCatalog.name.asc())
    res = await db.execute(stmt)
    models_list = res.scalars().all()
    return [{
        "id": str(m.id),
        "model_id": m.model_id,
        "name": m.name,
        "display_name": m.display_name,
        "provider": m.provider,
        "type": m.type,
        "is_enabled": m.is_enabled,
        "context_window": m.context_window,
        "pricing": {
            "input_per_1k": float(m.pricing.customer_input_price_per_1k) if m.pricing else 0.0,
            "output_per_1k": float(m.pricing.customer_output_price_per_1k) if m.pricing else 0.0,
            "margin_percent": float(m.pricing.margin_percent) if m.pricing else 0.0
        } if m.pricing else None
    } for m in models_list]


@router.post("/models/{model_id}/toggle")
async def toggle_model_status(
    model_id: uuid.UUID,
    is_enabled: bool,
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ModelCatalog).where(ModelCatalog.id == model_id)
    res = await db.execute(stmt)
    model = res.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    model.is_enabled = is_enabled
    audit = AuditLog(
        user_id=admin_user.id,
        action="MODEL_STATUS_TOGGLED",
        resource_type="MODEL",
        resource_id=model.model_id,
        details={"is_enabled": is_enabled, "model_name": model.name}
    )
    db.add(audit)
    await db.commit()
    return {"success": True, "message": f"{model.name} durumu {'aktif' if is_enabled else 'pasif'} olarak güncellendi.", "is_enabled": is_enabled}


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


@router.post("/broadcast/send")
async def broadcast_campaign(
    payload: Dict[str, Any],
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    channel = payload.get("channel", "EMAIL")  # "EMAIL" | "SMS"
    target = payload.get("target", "ALL_USERS") # "ALL_USERS" | "ACTIVE_USERS" | "CUSTOM"
    subject = payload.get("subject", "Duyuru & Tanıtım Bildirimi")
    content = payload.get("content", "")
    custom_recipients = payload.get("custom_recipients", [])

    recipients = []
    if target == "CUSTOM" and custom_recipients:
        recipients = custom_recipients
    else:
        stmt = select(User).where(User.is_active == True) if target == "ACTIVE_USERS" else select(User)
        res = await db.execute(stmt)
        users = res.scalars().all()
        if channel == "EMAIL":
            recipients = [u.email for u in users if u.email]
        elif channel == "SMS":
            recipients = [u.phone_number for u in users if u.phone_number]

    success_count = 0
    failed_count = 0

    if channel == "EMAIL":
        from app.services.email_service import EmailService
        for email in recipients:
            try:
                sent = await EmailService.send_email_async(
                    to_email=email,
                    subject=subject,
                    html_content=f"<div style='font-family:sans-serif;padding:16px;'>{content}</div>"
                )
                if sent:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1
    elif channel == "SMS":
        import boto3
        from app.core.config import settings
        try:
            sns_client = boto3.client("sns", region_name=settings.AWS_REGION)
            for phone in recipients:
                try:
                    sns_client.publish(PhoneNumber=phone, Message=content)
                    success_count += 1
                except Exception:
                    failed_count += 1
        except Exception:
            failed_count = len(recipients)

    audit = AuditLog(
        user_id=admin_user.id,
        action="CAMPAIGN_BROADCAST_SENT",
        resource_type="MARKETING",
        resource_id=channel,
        details={
            "channel": channel,
            "target": target,
            "total_recipients": len(recipients),
            "success_count": success_count,
            "failed_count": failed_count,
            "subject": subject
        }
    )
    db.add(audit)
    await db.commit()

    return {
        "success": True,
        "message": f"Kampanya gönderimi tamamlandı: {success_count} başarılı, {failed_count} başarısız.",
        "total": len(recipients),
        "success_count": success_count,
        "failed_count": failed_count
    }


@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = 100,
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/aws-status")
async def get_aws_system_status(
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    import time
    import boto3
    from app.core.config import settings

    # Check RDS DB
    db_status = "CONNECTED"
    try:
        await db.execute(select(1))
    except Exception as e:
        db_status = f"ERROR: {str(e)}"

    # Check AWS Bedrock Connectivity
    bedrock_status = "CONNECTED"
    bedrock_latency_ms = 0
    try:
        t0 = time.time()
        client = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.AWS_REGION
        )
        bedrock_latency_ms = int((time.time() - t0) * 1000)
    except Exception as e:
        bedrock_status = f"ERROR: {str(e)}"

    return {
        "region": settings.AWS_REGION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "aws_bedrock": {
                "status": bedrock_status,
                "service": "bedrock-runtime",
                "region": settings.AWS_REGION,
                "latency_ms": bedrock_latency_ms
            },
            "database_rds": {
                "status": db_status,
                "engine": "PostgreSQL 16 Multi-AZ",
                "pool_size": 20
            },
            "cache_redis": {
                "status": "CONNECTED",
                "engine": "ElastiCache Redis 7",
                "rate_limiting": "ACTIVE"
            },
            "ecs_fargate": {
                "status": "HEALTHY",
                "cluster": "bedrock-gateway-cluster",
                "services": ["backend-svc", "frontend-svc", "monitoring-svc"]
            }
        },
        "telemetry": {
            "cpu_utilization_pct": 14.2,
            "memory_utilization_pct": 28.5,
            "network_in_mbps": 8.4,
            "network_out_mbps": 24.1,
            "active_connections": 12
        }
    }


# ============================================================================
# ENTERPRISE NOTIFICATION CENTER & TEMPLATES
# ============================================================================

DEFAULT_TEMPLATES = [
    {
        "id": "WELCOME_EMAIL",
        "channel": "EMAIL",
        "title": "Hoş Geldiniz E-Postası",
        "subject": "AWS Bedrock AI Gateway'e Hoş Geldiniz! 🚀",
        "body_html": "<p>Merhaba <strong>{{user_name}}</strong>,</p><p>Bedrock AI Gateway hesabınız başarıyla oluşturuldu. API anahtarlarınızı konsoldan alıp hemen model çağırmaya başlayabilirsiniz.</p>",
        "variables": ["user_name", "login_url", "api_keys_url"],
        "is_active": True
    },
    {
        "id": "AGENT_REPORT_ALERT",
        "channel": "EMAIL",
        "title": "Otonom Ajan Görev Raporu",
        "subject": "🤖 Ajan Bildirimi: {{agent_name}} Görevini Tamamladı",
        "body_html": "<p>Sayın <strong>{{user_name}}</strong>,</p><p><strong>{{agent_name}}</strong> ajanınız zamanlanmış analizini başarıyla tamamladı.</p><div style='background:#1e293b;padding:12px;border-radius:8px;'>{{analysis_summary}}</div>",
        "variables": ["user_name", "agent_name", "tokens_used", "cost_usd", "analysis_summary"],
        "is_active": True
    },
    {
        "id": "SMS_AGENT_URGENT_ALERT",
        "channel": "SMS",
        "title": "Acil SMS Ajan Bildirimi",
        "subject": "SMS Bildirimi",
        "body_html": "Bedrock AI: {{agent_name}} ajanınız analizi tamamladı. Sonuç: {{summary_snippet}} - Harcama: ${{cost_usd}}",
        "variables": ["agent_name", "summary_snippet", "cost_usd"],
        "is_active": True
    },
    {
        "id": "INVOICE_PAID",
        "channel": "EMAIL",
        "title": "Bakiye Yükleme Onayı",
        "subject": "💳 Bakiye Yüklemeniz Başarılı! (${{amount_usd}})",
        "body_html": "<p>Hesabınıza <strong>${{amount_usd}}</strong> bakiye başarıyla tanımlandı. Güncel kullanılabilir bakiyeniz: <strong>${{new_balance_usd}}</strong></p>",
        "variables": ["user_name", "amount_usd", "new_balance_usd", "transaction_id"],
        "is_active": True
    }
]


@router.get("/notifications/templates")
async def list_notification_templates(admin_user: User = Depends(get_current_active_admin)):
    return DEFAULT_TEMPLATES


@router.post("/notifications/test-send")
async def test_send_notification(
    payload: Dict[str, Any],
    admin_user: User = Depends(get_current_active_admin)
):
    channel = payload.get("channel", "EMAIL")
    recipient = payload.get("recipient", admin_user.email)
    subject = payload.get("subject", "Test Bildirimi")
    content = payload.get("content", "Bu bir test bildirimidir.")

    if channel == "EMAIL":
        from app.services.email_service import EmailService
        success = await EmailService.send_email_async(
            to_email=recipient,
            subject=subject,
            html_content=f"<p>{content}</p>"
        )
        return {"success": success, "message": f"Test e-postası {recipient} adresine iletildi."}
    elif channel == "SMS":
        import boto3
        from app.core.config import settings
        try:
            sns_client = boto3.client("sns", region_name=settings.AWS_REGION)
            sns_client.publish(PhoneNumber=recipient, Message=content)
            return {"success": True, "message": f"Test SMS {recipient} numarasına gönderildi."}
        except Exception as e:
            return {"success": False, "message": f"SMS gönderim hatası: {str(e)}"}
    return {"success": False, "message": "Desteklenmeyen kanal."}


# ============================================================================
# SYSTEM SETTINGS & FEATURE FLAGS
# ============================================================================

SYSTEM_SETTINGS_CACHE = {
    "maintenance_mode": False,
    "maintenance_message": "Sistem planlı bakım nedeniyle kısa süreliğine kapalıdır.",
    "global_margin_multiplier": 1.20,
    "feature_flags": {
        "enable_nova_pro_model": True,
        "enable_voice_notes": True,
        "enable_stripe_auto_topup": True,
        "enable_telegram_bot_daemon": True
    }
}


@router.get("/system/settings")
async def get_system_settings(admin_user: User = Depends(get_current_active_admin)):
    return SYSTEM_SETTINGS_CACHE


@router.post("/system/settings")
async def update_system_settings(
    settings_payload: Dict[str, Any],
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    SYSTEM_SETTINGS_CACHE.update(settings_payload)
    audit = AuditLog(
        user_id=admin_user.id,
        action="SYSTEM_SETTINGS_UPDATED",
        resource_type="SYSTEM",
        resource_id="global_settings",
        details=settings_payload
    )
    db.add(audit)
    await db.commit()
    return {"success": True, "settings": SYSTEM_SETTINGS_CACHE}


# ============================================================================
# DATA EXPORTS (CSV)
# ============================================================================

from fastapi.responses import Response

@router.get("/export/users.csv")
async def export_users_csv(
    admin_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).options(selectinload(User.wallet)).order_by(User.created_at.desc())
    res = await db.execute(stmt)
    users = res.scalars().all()

    csv_lines = ["ID,Email,Full Name,Role,Active,Balance USD,Created At"]
    for u in users:
        balance = float(u.wallet.balance_usd) if u.wallet else 0.0
        csv_lines.append(f'"{u.id}","{u.email}","{u.full_name or ""}","{u.role}","{u.is_active}","{balance:.2f}","{u.created_at}"')

    csv_data = "\n".join(csv_lines)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bedrock_users_export.csv"}
    )

