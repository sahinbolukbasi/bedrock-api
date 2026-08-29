import uuid
import secrets
import string
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
from app.services.telegram_bot import TelegramBotService, get_telegram_bot_username, get_telegram_bot_token
from app.services.scheduler import AgentAutonomousEngine
from loguru import logger

router = APIRouter()


class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    icon: Optional[str] = "🤖"
    agent_type: Optional[str] = "custom"
    goal_definition: Optional[str] = ""
    autonomy_level: Optional[str] = "AUTONOMOUS"  # "AUTONOMOUS", "CONFIRMATION_REQUIRED", "ADVISORY"
    description: Optional[str] = None
    model_id: str = "amazon.nova-micro-v1:0"
    system_prompt: str = Field(min_length=5)
    schedule_cron: Optional[str] = None
    schedule_enabled: bool = False
    learned_memory_cache: Optional[str] = ""
    memory_settings: Dict[str, Any] = Field(default_factory=lambda: {"compression": True, "max_context": 4000})
    tools_config: Dict[str, Any] = Field(default_factory=dict)  # {"web_search": true, "telegram": true, "email": false}
    knowledge_sources: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    agent_type: Optional[str] = None
    goal_definition: Optional[str] = None
    autonomy_level: Optional[str] = None
    description: Optional[str] = None
    model_id: Optional[str] = None
    system_prompt: Optional[str] = None
    schedule_cron: Optional[str] = None
    schedule_enabled: Optional[bool] = None
    learned_memory_cache: Optional[str] = None
    memory_settings: Optional[Dict[str, Any]] = None
    tools_config: Optional[Dict[str, Any]] = None
    knowledge_sources: Optional[List[Dict[str, Any]]] = None


class AgentRunRequest(BaseModel):
    input_text: str
    trigger_email: bool = False
    telegram_notify: bool = True


# =====================================================================
# AGENT CRUD ENDPOINTS
# =====================================================================
@router.get("", include_in_schema=False)
@router.get("/")
async def list_user_agents(
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user:
        stmt = select(CustomAgent).where(CustomAgent.user_id == current_user.id).order_by(CustomAgent.created_at.desc())
    else:
        stmt = select(CustomAgent).order_by(CustomAgent.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("", include_in_schema=False)
@router.post("/")
async def create_agent(
    body: AgentCreateRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        u_stmt = select(User).where(User.is_active == True).order_by(User.created_at.asc()).limit(1)
        res = await db.execute(u_stmt)
        current_user = res.scalars().first()

    if not current_user:
        raise HTTPException(status_code=401, detail="Lütfen önce giriş yapın.")

    agent = CustomAgent(
        user_id=current_user.id,
        name=body.name,
        icon=body.icon or "🤖",
        agent_type=body.agent_type or "custom",
        goal_definition=body.goal_definition or "",
        autonomy_level=body.autonomy_level or "AUTONOMOUS",
        description=body.description,
        model_id=body.model_id,
        system_prompt=body.system_prompt,
        schedule_cron=body.schedule_cron,
        schedule_enabled=body.schedule_enabled,
        learned_memory_cache=body.learned_memory_cache or "",
        memory_settings=body.memory_settings or {},
        tools_config=body.tools_config or {},
        knowledge_sources=body.knowledge_sources or []
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
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CustomAgent).where(CustomAgent.id == agent_id)
    if current_user:
        stmt = stmt.where(CustomAgent.user_id == current_user.id)
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
    if body.goal_definition is not None:
        agent.goal_definition = body.goal_definition
    if body.autonomy_level is not None:
        agent.autonomy_level = body.autonomy_level
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
    if body.learned_memory_cache is not None:
        agent.learned_memory_cache = body.learned_memory_cache
    if body.memory_settings is not None:
        agent.memory_settings = body.memory_settings
    if body.tools_config is not None:
        agent.tools_config = body.tools_config
    if body.knowledge_sources is not None:
        agent.knowledge_sources = body.knowledge_sources

    await db.commit()
    await db.refresh(agent)
    return agent



@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CustomAgent).where(CustomAgent.id == agent_id)
    if current_user:
        stmt = stmt.where(CustomAgent.user_id == current_user.id)
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
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        u_stmt = select(User).where(User.is_active == True).order_by(User.created_at.asc()).limit(1)
        res = await db.execute(u_stmt)
        current_user = res.scalars().first()

    stmt = select(CustomAgent).where(CustomAgent.id == agent_id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    result = await AgentAutonomousEngine.run_agent(
        agent=agent,
        input_text=body.input_text,
        trigger_type="MANUAL_CONSOLE",
        db=db,
        telegram_chat_id=current_user.telegram_chat_id if (current_user and body.telegram_notify) else None
    )
    return result


@router.get("/{agent_id}/logs")
async def get_agent_logs(
    agent_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AgentExecutionLog).where(AgentExecutionLog.agent_id == agent_id).order_by(AgentExecutionLog.created_at.desc()).limit(25)
    res = await db.execute(stmt)
    return res.scalars().all()



@router.post("/{agent_id}/knowledge")
async def add_knowledge_source(
    agent_id: uuid.UUID,
    body: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests and indexes custom URL, REST API, or raw text into agent's knowledge base.
    """
    from app.services.local_rag import LocalRAGEngine
    from app.services.agent_growth import AgentGrowthEngine

    stmt = select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.user_id == current_user.id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    stype = body.get("type", "text")  # "url", "api", "text"
    sname = body.get("name", "Custom Knowledge")
    scontent = body.get("content", "")

    cached_chunks = []
    if stype == "url" and scontent.startswith("http"):
        chunks = await LocalRAGEngine.ingest_url(scontent)
        cached_chunks = [c.to_dict() for c in chunks]
    elif stype == "api" and scontent.startswith("http"):
        chunks = await LocalRAGEngine.ingest_api_endpoint(scontent, headers=body.get("headers"))
        cached_chunks = [c.to_dict() for c in chunks]
    elif stype == "text":
        chunks = LocalRAGEngine.chunk_text(scontent, sname)
        cached_chunks = [c.to_dict() for c in chunks]

    sources = list(agent.knowledge_sources or [])
    new_source = {
        "id": str(uuid.uuid4())[:8],
        "type": stype,
        "name": sname,
        "content": scontent,
        "chunk_count": len(cached_chunks),
        "cached_chunks": cached_chunks[:20],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    sources.append(new_source)
    agent.knowledge_sources = sources

    # Award XP for Knowledge Ingestion (+40 XP)
    growth = AgentGrowthEngine.award_xp(
        agent.xp_points or 0,
        AgentGrowthEngine.XP_REWARD_KNOWLEDGE_SOURCE_ADDED,
        f"Yeni bilgi kaynağı eklendi: {sname}",
        agent.growth_history
    )
    agent.xp_points = growth["new_xp"]
    agent.level = growth["level"]
    agent.evolution_stage = growth["stage"]
    agent.growth_history = growth["growth_history"]

    await db.commit()
    await db.refresh(agent)
    return {"message": "Knowledge source indexed successfully", "source": new_source, "growth": growth}


@router.delete("/{agent_id}/knowledge/{source_id}")
async def remove_knowledge_source(
    agent_id: uuid.UUID,
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.user_id == current_user.id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    sources = [s for s in (agent.knowledge_sources or []) if s.get("id") != source_id]
    agent.knowledge_sources = sources
    await db.commit()
    return {"message": "Knowledge source removed successfully"}


@router.post("/{agent_id}/feedback")
async def submit_agent_feedback(
    agent_id: uuid.UUID,
    body: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.services.agent_growth import AgentGrowthEngine
    stmt = select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.user_id == current_user.id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    is_positive = bool(body.get("is_positive", True))
    note = body.get("note", "")

    if is_positive:
        growth = AgentGrowthEngine.award_xp(
            agent.xp_points or 0,
            AgentGrowthEngine.XP_REWARD_USER_UPVOTE,
            f"Kullanıcı beğenisi ve olumlu geri bildirim: {note}",
            agent.growth_history
        )
        agent.xp_points = growth["new_xp"]
        agent.level = growth["level"]
        agent.evolution_stage = growth["stage"]
        agent.growth_history = growth["growth_history"]
        await db.commit()
        return {"message": "Thank you! Bot gained +50 XP and improved.", "growth": growth}

    return {"message": "Feedback recorded."}


@router.get("/{agent_id}/growth")
async def get_agent_growth_stats(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.services.agent_growth import AgentGrowthEngine
    stmt = select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.user_id == current_user.id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    lvl, stage, min_xp, max_xp, progress = AgentGrowthEngine.calculate_level_and_stage(agent.xp_points or 0)
    facts_count = len((agent.learned_memory_cache or "").splitlines())
    iq_score = AgentGrowthEngine.calculate_iq_score(
        agent.total_runs or 0,
        facts_count,
        len(agent.knowledge_sources or []),
        lvl
    )

    return {
        "xp_points": agent.xp_points or 0,
        "level": lvl,
        "evolution_stage": stage,
        "progress_pct": progress,
        "min_xp": min_xp,
        "next_level_xp": max_xp,
        "iq_score": iq_score,
        "total_runs": agent.total_runs or 0,
        "knowledge_count": len(agent.knowledge_sources or []),
        "growth_history": agent.growth_history or []
    }

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
    Always generates and returns an active pairing code and direct 1-click deep link.
    """
    if not current_user:
        u_stmt = select(User).where(User.is_active == True).order_by(User.created_at.asc()).limit(1)
        res = await db.execute(u_stmt)
        current_user = res.scalar_one_or_none()

    if current_user:
        pairing_code = current_user.telegram_pairing_code
        if not pairing_code:
            pairing_code = await TelegramBotService.generate_pairing_code(current_user.id, db)

        bot_user = get_telegram_bot_username()
        return {
            "is_connected": bool(current_user.telegram_chat_id),
            "chat_id": current_user.telegram_chat_id,
            "username": current_user.telegram_username,
            "pairing_code": pairing_code,
            "bot_username": bot_user,
            "deep_link": f"https://t.me/{bot_user}?start={pairing_code}"
        }

    digits = "".join(secrets.choice(string.digits) for _ in range(6))
    fallback_code = f"TG-{digits}"
    bot_user = get_telegram_bot_username()
    return {
        "is_connected": False,
        "chat_id": None,
        "username": None,
        "pairing_code": fallback_code,
        "bot_username": bot_user,
        "deep_link": f"https://t.me/{bot_user}?start={fallback_code}"
    }


@router.post("/telegram/generate-code")
async def generate_telegram_pairing_code(
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        u_stmt = select(User).where(User.is_active == True).order_by(User.created_at.asc()).limit(1)
        res = await db.execute(u_stmt)
        current_user = res.scalar_one_or_none()

    if current_user:
        code = await TelegramBotService.generate_pairing_code(current_user.id, db)
    else:
        digits = "".join(secrets.choice(string.digits) for _ in range(6))
        code = f"TG-{digits}"

    bot_user = get_telegram_bot_username()
    return {
        "pairing_code": code,
        "deep_link": f"https://t.me/{bot_user}?start={code}",
        "bot_username": bot_user
    }


@router.post("/telegram/disconnect")
async def disconnect_telegram(
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        u_stmt = select(User).where(User.is_active == True).order_by(User.created_at.asc()).limit(1)
        res = await db.execute(u_stmt)
        current_user = res.scalar_one_or_none()

    if current_user:
        current_user.telegram_chat_id = None
        current_user.telegram_username = None
        digits = "".join(secrets.choice(string.digits) for _ in range(6))
        new_code = f"TG-{digits}"
        current_user.telegram_pairing_code = new_code
        await db.commit()
    else:
        digits = "".join(secrets.choice(string.digits) for _ in range(6))
        new_code = f"TG-{digits}"

    bot_user = get_telegram_bot_username()
    return {
        "status": "disconnected",
        "message": "Telegram bağlantısı başarıyla kesildi.",
        "pairing_code": new_code,
        "deep_link": f"https://t.me/{bot_user}?start={new_code}",
        "bot_username": bot_user
    }




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
    token_to_use = bot_token or get_telegram_bot_token()
    result = await TelegramBotService.process_webhook_update(token_to_use, update, db)
    return result
