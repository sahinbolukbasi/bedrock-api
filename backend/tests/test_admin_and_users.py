import pytest
import uuid
from decimal import Decimal
from app.domain.schemas import (
    AdminBalanceAdjustRequest,
    AdminNotifyUserRequest,
    AdminOverviewStats
)
from app.services.email_service import EmailService


def test_admin_schemas_and_validation():
    # 1. Admin overview schema validation
    overview = AdminOverviewStats(
        total_users=12,
        active_api_keys=8,
        total_revenue_usd=Decimal("150.75"),
        total_provider_cost_usd=Decimal("60.25"),
        platform_net_profit_usd=Decimal("90.50"),
        total_requests=1240,
        total_tokens_served=450000,
        avg_latency_ms=185.5
    )
    assert overview.total_users == 12
    assert overview.total_revenue_usd == Decimal("150.75")
    assert overview.platform_net_profit_usd == Decimal("90.50")

    # 2. Balance adjust schema validation
    bal_req = AdminBalanceAdjustRequest(new_balance_usd=Decimal("250.00"))
    assert bal_req.new_balance_usd == Decimal("250.00")

    # 3. User notification request validation
    notify_req = AdminNotifyUserRequest(
        title="Güvenlik Bildirimi",
        message="Hesabınıza $50 bakiye tanımlandı.",
        channel="EMAIL"
    )
    assert notify_req.title == "Güvenlik Bildirimi"
    assert notify_req.channel == "EMAIL"


@pytest.mark.asyncio
async def test_admin_direct_user_email_notification():
    recipient = "testuser@startup.io"
    title = "AWS Bedrock Kredi Tanımlaması"
    message = "Sayın kullanıcımız, hesabınıza $100.00 test kredisi tanımlanmıştır."
    
    html = EmailService._render_base_template(
        title,
        "Yönetici Bildirimi",
        f"<h2 style='color:#ffffff;'>{title}</h2><p>{message}</p>"
    )
    assert title in html
    assert message in html
    assert "Bedrock" in html

    # Send async email
    sent = await EmailService.send_email_async(recipient, f"[Bedrock Gateway] {title}", html)
    assert sent is True
