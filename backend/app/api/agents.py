import uuid
import httpx
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.entities import User, CustomAgent, AgentExecutionLog, Wallet
from app.services.email_service import EmailService
from app.services.telegram_bot import TelegramBotService, DEFAULT_TELEGRAM_BOT_USERNAME, DEFAULT_TELEGRAM_BOT_TOKEN
from app.services.scheduler import AgentAutonomousEngine
from loguru import logger

router = APIRouter()


class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    icon: Optional[str] = "🤖"
    agent_type: Optional[str] = "custom"
    description: Optional[str] = None
    model_id: str = "amazon.nova-micro-v1:0"
    system_prompt: str = Field(min_length=5)
    schedule_cron: Optional[str] = None
    schedule_enabled: bool = False
    learned_memory_cache: Optional[str] = ""
    tools_config: Dict[str, Any] = Field(default_factory=dict)  # {"web_search": true, "telegram": true, "email": false}


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    agent_type: Optional[str] = None
    description: Optional[str] = None
    model_id: Optional[str] = None
    system_prompt: Optional[str] = None
    schedule_cron: Optional[str] = None
    schedule_enabled: Optional[bool] = None
    tools_config: Optional[Dict[str, Any]] = None


class AgentRunRequest(BaseModel):
    input_text: str
    trigger_email: bool = False
    telegram_notify: bool = True


# =====================================================================
# AGENT CRUD ENDPOINTS
# =====================================================================

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
        icon=body.icon or "🤖",
        agent_type=body.agent_type or "custom",
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


@router.patch("/{agent_id}")
@router.put("/{agent_id}")
async def update_agent(
    agent_id: uuid.UUID,
    body: AgentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.user_id == current_user.id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if body.name is not None:
        agent.name = body.name
    if body.icon is not None:
        agent.icon = body.icon
    if body.agent_type is not None:
        agent.agent_type = body.agent_type
    if body.description is not None:
        agent.description = body.description
    if body.model_id is not None:
        agent.model_id = body.model_id
    if body.system_prompt is not None:
        agent.system_prompt = body.system_prompt
    if body.schedule_cron is not None:
        agent.schedule_cron = body.schedule_cron
    if body.schedule_enabled is not None:
        agent.schedule_enabled = body.schedule_enabled
    if body.tools_config is not None:
        agent.tools_config = body.tools_config

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
        trigger_type="MANUAL_CONSOLE",
        db=db,
        telegram_chat_id=current_user.telegram_chat_id if body.telegram_notify else None
    )
    return result


@router.get("/{agent_id}/logs")
async def get_agent_logs(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AgentExecutionLog).where(AgentExecutionLog.agent_id == agent_id).order_by(AgentExecutionLog.created_at.desc()).limit(25)
    res = await db.execute(stmt)
    return res.scalars().all()


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
    return {"message": "Agent memory reset successfully"}


# =====================================================================
# TELEGRAM INTEGRATION & PAIRING SYSTEM
# =====================================================================

@router.get("/telegram/status")
async def get_telegram_status(
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns current Telegram connection status, chat ID, username, and active pairing code.
    Always generates a valid pairing code even in demo / initial launch state.
    """
    if not current_user:
        # Resolve or create demo/guest user
        u_stmt = select(User).where(User.is_active == True).limit(1)
        res = await db.execute(u_stmt)
        current_user = res.scalar_one_or_none()

    if current_user:
        pairing_code = current_user.telegram_pairing_code
        if not pairing_code and not current_user.telegram_chat_id:
            pairing_code = await TelegramBotService.generate_pairing_code(current_user.id, db)

        return {
            "is_connected": bool(current_user.telegram_chat_id),
            "chat_id": current_user.telegram_chat_id,
            "username": current_user.telegram_username,
            "pairing_code": pairing_code,
            "bot_username": DEFAULT_TELEGRAM_BOT_USERNAME,
            "deep_link": f"https://t.me/{DEFAULT_TELEGRAM_BOT_USERNAME}?start={pairing_code}" if pairing_code else f"https://t.me/{DEFAULT_TELEGRAM_BOT_USERNAME}"
        }

    # Fallback pairing code
    fallback_code = "TG-" + "".join(random.choices(string.digits, k=6))
    return {
        "is_connected": False,
        "chat_id": None,
        "username": None,
        "pairing_code": fallback_code,
        "bot_username": DEFAULT_TELEGRAM_BOT_USERNAME,
        "deep_link": f"https://t.me/{DEFAULT_TELEGRAM_BOT_USERNAME}?start={fallback_code}"
    }


@router.post("/telegram/generate-code")
async def generate_telegram_pairing_code(
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        u_stmt = select(User).where(User.is_active == True).limit(1)
        res = await db.execute(u_stmt)
        current_user = res.scalar_one_or_none()

    if current_user:
        code = await TelegramBotService.generate_pairing_code(current_user.id, db)
    else:
        code = "TG-" + "".join(random.choices(string.digits, k=6))

    return {
        "pairing_code": code,
        "deep_link": f"https://t.me/{DEFAULT_TELEGRAM_BOT_USERNAME}?start={code}"
    }



@router.post("/telegram/disconnect")
async def disconnect_telegram(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    current_user.telegram_chat_id = None
    current_user.telegram_username = None
    current_user.telegram_pairing_code = None
    await db.commit()
    return {"message": "Telegram connection removed successfully"}


@router.post("/telegram/test")
async def test_telegram_message(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.telegram_chat_id:
        raise HTTPException(status_code=400, detail="Telegram hesabınız henüz bağlı değil. Lütfen önce eşleştirin.")

    test_msg = (
        "🔔 *AWS Bedrock AI Gateway — Test Bildirimi*\n\n"
        "✅ Telegram entegrasyonunuz başarıyla çalışıyor!\n"
        "Artık oluşturduğunuz otonom botlar (Haber takibi, Analizler, Raporlar) bu kanala anlık bildirim gönderecektir."
    )
    success = await TelegramBotService.send_message(
        bot_token=None,
        chat_id=current_user.telegram_chat_id,
        text=test_msg
    )
    if not success:
        raise HTTPException(status_code=502, detail="Telegram bildirimi gönderilemedi. Lütfen botu başlattığınızdan emin olun.")

    return {"message": "Test message sent to Telegram successfully"}


@router.post("/telegram/webhook")
async def telegram_bot_webhook(
    update: Dict[str, Any] = Body(...),
    bot_token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    token_to_use = bot_token or DEFAULT_TELEGRAM_BOT_TOKEN
    result = await TelegramBotService.process_webhook_update(token_to_use, update, db)
    return result
