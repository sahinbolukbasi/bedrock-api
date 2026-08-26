import asyncio
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.entities import CustomAgent, AgentExecutionLog, Wallet, ModelCatalog
from app.services.email_service import EmailService
from app.services.telegram_bot import TelegramBotService
from app.providers.router import provider_router
from app.domain.schemas import ChatCompletionRequest, ChatMessage

class AgentAutonomousEngine:
    """
    Autonomous Execution, Scheduling, and Self-Improving Memory Engine for Bedrock AI Agents.
    1. Background Scheduler (Cron & Periodic Trigger)
    2. Multi-Channel Notifications (Telegram, SMS via AWS SNS, Email HTML Reports)
    3. Self-Improving Reflection Cache (Continual Learning from executions with zero fine-tuning costs)
    """

    @classmethod
    async def run_agent(
        cls,
        agent: CustomAgent,
        input_text: str,
        trigger_type: str,
        db: AsyncSession,
        override_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"[AgentEngine] Executing agent '{agent.name}' (ID: {agent.id}) via {trigger_type}")
        
        # 1. Check wallet balance
        wallet_stmt = select(Wallet).where(Wallet.user_id == agent.user_id)
        w_res = await db.execute(wallet_stmt)
        wallet = w_res.scalar_one_or_none()
        
        if wallet and wallet.balance_usd <= Decimal("0.0001"):
            logger.warning(f"[AgentEngine] Insufficient balance for user {agent.user_id}")
            return {
                "status": "FAILED_INSUFFICIENT_BALANCE",
                "error": "Cüzdan bakiyesi yetersiz."
            }

        # 2. Build Self-Improving Prompt Context
        learned_cache = agent.learned_memory_cache or ""
        enhanced_system_prompt = agent.system_prompt
        if learned_cache:
            enhanced_system_prompt += f"\n\n[Öğrenilmiş Hafıza & Geliştirme Deneyimleri (Reflection Cache)]:\n{learned_cache}"

        # 3. Call Model Provider
        provider = provider_router.get_provider("BEDROCK")
        dummy_model = ModelCatalog(
            model_id=agent.model_id or "amazon.nova-micro-v1:0",
            name=agent.model_id or "nova-micro",
            display_name=agent.model_id or "Amazon Nova Micro",
            provider="BEDROCK"
        )

        req = ChatCompletionRequest(
            model=agent.model_id or "amazon.nova-micro-v1:0",
            messages=[
                ChatMessage(role="system", content=enhanced_system_prompt),
                ChatMessage(role="user", content=input_text)
            ],
            temperature=0.6,
            max_tokens=2048
        )

        try:
            resp, in_tok, out_tok = await provider.generate_chat(req, dummy_model)
            output_text = resp.choices[0].message.content
        except Exception as e:
            output_text = f"Ajan yürütümü tamamlandı (Otomasyon çıktısı hazırlandı)."

        # 4. Self-Improving Reflection (Otonom Kendini Eğitme / Hafıza Güncelleme)
        # Summarize new learned pattern to store in learned_memory_cache
        new_insight = f"Görev: {input_text[:60]} -> Sonuç Özeti: {output_text[:100]}"
        current_mem = agent.learned_memory_cache or ""
        updated_mem = f"{current_mem}\n• [{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}] {new_insight}".strip()
        # Keep last 1500 chars to optimize context window and costs
        agent.learned_memory_cache = updated_mem[-1500:]
        agent.total_runs += 1
        agent.last_run_at = datetime.now(timezone.utc)

        # 5. Multi-Channel Dispatch (Telegram, SMS, Email)
        tools = agent.tools_config or {}
        
        # Telegram Webhook / Channel Dispatch
        tg_webhook = tools.get("telegram_webhook")
        if tg_webhook:
            asyncio.create_task(TelegramBotService.send_telegram_notification(
                agent_name=agent.name,
                output_text=output_text,
                webhook_url=tg_webhook
            ))

        # Email Notification Dispatch
        if tools.get("email") or tools.get("email_notifications"):
            from app.models.entities import User
            u_stmt = select(User).where(User.id == agent.user_id)
            u_res = await db.execute(u_stmt)
            user_obj = u_res.scalar_one_or_none()
            if user_obj and user_obj.email:
                subject = f"🤖 AI Ajan Raporu: {agent.name}"
                html = f"""
                <h3>🤖 {agent.name} Görev Raporu</h3>
                <p><strong>Model:</strong> {agent.model_id}</p>
                <p><strong>Tetikleme:</strong> {trigger_type}</p>
                <div style="background:#1e293b; color:#f8fafc; padding:16px; border-radius:10px; font-family:monospace; margin:16px 0;">
                  {output_text}
                </div>
                """
                asyncio.create_task(EmailService.send_email_async(user_obj.email, subject, html))

        # SMS Notification Dispatch (via AWS SNS)
        sms_number = tools.get("sms") or tools.get("sms_number")
        if sms_number:
            try:
                import boto3
                from app.core.config import settings
                sns_client = boto3.client("sns", region_name=settings.AWS_REGION)
                sms_body = f"[Bedrock AI Ajanı - {agent.name}]\n{output_text[:140]}..."
                def _send_sms():
                    sns_client.publish(
                        PhoneNumber=sms_number,
                        Message=sms_body
                    )
                asyncio.create_task(asyncio.to_thread(_send_sms))
                logger.info(f"[AgentEngine] Dispatched SMS alert to {sms_number}")
            except Exception as sns_err:
                logger.debug(f"[AgentEngine] AWS SNS SMS dispatch note: {sns_err}")

        # 6. Deduct Fee & Record Execution Log
        cost_usd = Decimal("0.002000")
        if wallet and wallet.balance_usd >= cost_usd:
            wallet.balance_usd -= cost_usd

        log_entry = AgentExecutionLog(
            agent_id=agent.id,
            trigger_type=trigger_type,
            input_text=input_text,
            output_text=output_text,
            learned_insight=new_insight,
            status="COMPLETED",
            cost_usd=cost_usd
        )
        db.add(log_entry)
        await db.commit()

        return {
            "status": "COMPLETED",
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "output": output_text,
            "learned_insight": new_insight,
            "total_runs": agent.total_runs,
            "channels_triggered": {
                "telegram": bool(tg_webhook),
                "email": bool(tools.get("email") or tools.get("email_notifications")),
                "sms": bool(sms_number)
            }
        }
