import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.entities import User, Conversation, Message

router = APIRouter()


class ConversationCreate(BaseModel):
    title: str = "New Chat"
    model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    system_prompt: Optional[str] = None
    temperature: float = 0.7


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None


class MessageCreate(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    tokens: int = 0
    cost_usd: Decimal = Decimal("0.000000")


@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/conversations")
async def create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    conv = Conversation(
        user_id=current_user.id,
        title=body.title,
        model_id=body.model_id,
        system_prompt=body.system_prompt,
        temperature=body.temperature
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("/conversations/{conv_id}/messages")
async def get_conversation_messages(
    conv_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Message)
        .join(Conversation)
        .where(Message.conversation_id == conv_id, Conversation.user_id == current_user.id)
        .order_by(Message.created_at.asc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.patch("/conversations/{conv_id}")
async def update_conversation(
    conv_id: uuid.UUID,
    body: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == current_user.id)
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if body.title is not None:
        conv.title = body.title
    if body.system_prompt is not None:
        conv.system_prompt = body.system_prompt
    if body.temperature is not None:
        conv.temperature = body.temperature

    await db.commit()
    await db.refresh(conv)
    return conv


@router.post("/conversations/{conv_id}/messages")
async def append_message(
    conv_id: uuid.UUID,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    conv_stmt = select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == current_user.id)
    conv_res = await db.execute(conv_stmt)
    conv = conv_res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg = Message(
        conversation_id=conv_id,
        role=body.role,
        content=body.content,
        tokens=body.tokens,
        cost_usd=body.cost_usd
    )
    db.add(msg)
    conv.updated_at = msg.created_at
    await db.commit()
    await db.refresh(msg)
    return msg


@router.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == current_user.id)
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    await db.commit()
    return {"message": "Conversation deleted"}
