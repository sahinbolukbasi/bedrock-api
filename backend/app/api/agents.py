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


from app.services.scheduler import AgentAutonomousEngine
from app.models.entities import AgentExecutionLog

class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: Optional[str] = None
    model_id: str = "amazon.nova-micro-v1:0"
    system_prompt: str = Field(min_length=5)
    schedule_cron: Optional[str] = None
    schedule_enabled: bool = False
    learned_memory_cache: Optional[str] = ""
    tools_config: Dict[str, Any] = Field(default_factory=dict)  # {"email": true, "sms": "+905...", "telegram_webhook": "..."}


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
        schedule_cron=body.schedule_cron,
        schedule_enabled=body.schedule_enabled,
        learned_memory_cache=body.learned_memory_cache or "",
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.user_id == current_user.id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    result = await AgentAutonomousEngine.run_agent(
        agent=agent,
        input_text=body.input_text,
        trigger_type="MANUAL_API",
        db=db
    )
    return result


@router.put("/{agent_id}/schedule")
async def update_agent_schedule(
    agent_id: uuid.UUID,
    cron: Optional[str] = None,
    enabled: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.user_id == current_user.id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.schedule_cron = cron or agent.schedule_cron
    agent.schedule_enabled = enabled
    await db.commit()
    return {"message": "Schedule updated successfully", "schedule_cron": agent.schedule_cron, "enabled": agent.schedule_enabled}


@router.post("/{agent_id}/reset-memory")
async def reset_agent_memory(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.user_id == current_user.id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.learned_memory_cache = ""
    await db.commit()
    return {"message": "Agent reflection memory cache reset successfully"}


@router.get("/{agent_id}/logs")
async def get_agent_logs(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AgentExecutionLog).where(AgentExecutionLog.agent_id == agent_id).order_by(AgentExecutionLog.created_at.desc()).limit(20)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/telegram/webhook")
async def telegram_bot_webhook(
    update: Dict[str, Any],
    bot_token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    from app.services.telegram_bot import TelegramBotService
    token_to_use = bot_token or "REDACTED_TELEGRAM_BOT_TOKEN"
    result = await TelegramBotService.process_webhook_update(token_to_use, update, db)
    return result
