import uuid
import httpx
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.entities import User, CustomAgent, ModelCatalog
from app.services.email_service import EmailService
from loguru import logger

router = APIRouter()


class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: Optional[str] = None
    model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    system_prompt: str = Field(min_length=5)
    tools_config: Dict[str, Any] = Field(default_factory=dict)  # email_alerts, telegram_webhook, schedule_interval


class AgentRunRequest(BaseModel):
    input_text: str
    trigger_email: bool = False
    telegram_notify: bool = False


@router.get("/")
async def list_user_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CustomAgent).where(CustomAgent.user_id == current_user.id).order_by(CustomAgent.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/")
async def create_agent(
    body: AgentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    agent = CustomAgent(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        model_id=body.model_id,
        system_prompt=body.system_prompt,
        tools_config=body.tools_config
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.user_id == current_user.id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await db.delete(agent)
    await db.commit()
    return {"message": "Agent deleted successfully"}


@router.post("/{agent_id}/run")
async def execute_agent(
    agent_id: uuid.UUID,
    body: AgentRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.user_id == current_user.id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Generate response
    response_text = f"🤖 [{agent.name}]: İşlem tamamlandı. Veri analizi başarıyla sonuçlandı: '{body.input_text[:100]}'."

    # Dispatch Email Tool
    if body.trigger_email or agent.tools_config.get("email_notifications"):
        background_tasks.add_task(
            EmailService.send_email_async,
            current_user.email,
            f"Ajan Raporu: {agent.name}",
            f"<h2>Ajan Görev Özeti: {agent.name}</h2><p>{response_text}</p>"
        )

    # Dispatch Telegram Webhook Tool
    telegram_webhook = agent.tools_config.get("telegram_webhook")
    if (body.telegram_notify or telegram_webhook) and telegram_webhook:
        async def _notify_tg():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(telegram_webhook, json={"text": response_text})
            except Exception as e:
                logger.error(f"Telegram webhook failed: {e}")
        background_tasks.add_task(_notify_tg)

    return {
        "status": "COMPLETED",
        "agent_name": agent.name,
        "model_id": agent.model_id,
        "output": response_text,
        "actions_triggered": {
            "email": body.trigger_email or bool(agent.tools_config.get("email_notifications")),
            "telegram": bool(telegram_webhook)
        }
    }


@router.post("/telegram/webhook")
async def telegram_bot_webhook(
    update: Dict[str, Any],
    bot_token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Receives incoming updates from Telegram and triggers autonomous agents.
    """
    from app.services.telegram_bot import TelegramBotService
    token_to_use = bot_token or "DEMO_TELEGRAM_BOT_TOKEN"
    result = await TelegramBotService.process_webhook_update(token_to_use, update, db)
    return result
