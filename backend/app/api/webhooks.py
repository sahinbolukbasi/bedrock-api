from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.entities import CustomAgent
import json
import httpx
from loguru import logger

router = APIRouter()

# Meta Webhook Doğrulama (GET)
@router.get("/meta")
async def verify_meta_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token:
        # Check if any agent has this verify token
        stmt = select(CustomAgent).where(CustomAgent.meta_verify_token == token)
        res = await db.execute(stmt)
        agent = res.scalar_one_or_none()
        
        if agent:
            return PlainTextResponse(challenge)
        else:
            raise HTTPException(status_code=403, detail="Invalid verify token")
            
    raise HTTPException(status_code=400, detail="Bad Request")


# Meta Webhook Gelen Mesajlar (POST)
@router.post("/meta")
async def handle_meta_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    body = await request.json()
    
    try:
        # Check if this is a WhatsApp or Instagram webhook
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    metadata = value.get("metadata", {})
                    phone_number_id = metadata.get("phone_number_id")
                    
                    if not phone_number_id:
                        continue
                        
                    # Find which agent this phone number belongs to
                    stmt = select(CustomAgent).where(CustomAgent.whatsapp_phone_id == phone_number_id)
                    res = await db.execute(stmt)
                    agent = res.scalar_one_or_none()
                    
                    if not agent:
                        logger.warning(f"No agent found for WhatsApp phone_number_id: {phone_number_id}")
                        continue
                        
                    # Parse messages and send to background task
                    messages = value.get("messages", [])
                    for msg in messages:
                        if msg.get("type") == "text":
                            text = msg.get("text", {}).get("body")
                            sender = msg.get("from")
                            
                            # Fire background task to process AI response
                            background_tasks.add_task(
                                process_whatsapp_message,
                                agent.id, sender, text, agent.whatsapp_token, phone_number_id
                            )
                            
        elif body.get("object") == "instagram":
            # Instagram Logic Here
            for entry in body.get("entry", []):
                account_id = entry.get("id")
                # Find agent by instagram_account_id
                stmt = select(CustomAgent).where(CustomAgent.instagram_account_id == account_id)
                res = await db.execute(stmt)
                agent = res.scalar_one_or_none()
                
                if not agent:
                    continue
                    
                messaging = entry.get("messaging", [])
                for event in messaging:
                    if event.get("message"):
                        sender_id = event["sender"]["id"]
                        text = event["message"].get("text")
                        
                        if text:
                            # Fire background task
                            background_tasks.add_task(
                                process_instagram_message,
                                agent.id, sender_id, text, agent.instagram_token
                            )
                            
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        # Always return 200 to Meta to prevent retries if it's an unhandled format
        return {"status": "error", "message": str(e)}


async def process_whatsapp_message(agent_id, sender_phone, text, token, phone_id):
    from app.services.scheduler import AgentAutonomousEngine
    from app.core.database import async_session_maker
    
    # We must use a new DB session since this is a background task
    async with async_session_maker() as db:
        stmt = select(CustomAgent).where(CustomAgent.id == agent_id)
        res = await db.execute(stmt)
        agent = res.scalar_one_or_none()
        
        if not agent:
            return
            
        # Run AI logic
        try:
            result = await AgentAutonomousEngine.run_agent(
                agent=agent,
                input_text=text,
                trigger_type="WHATSAPP",
                db=db,
                telegram_chat_id=None
            )
            ai_reply = result.get("response", "Üzgünüm, şu an yanıt veremiyorum.")
            
            # Send HTTP back to WhatsApp API
            url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": sender_phone,
                "type": "text",
                "text": {"body": ai_reply}
            }
            
            async with httpx.AsyncClient() as client:
                r = await client.post(url, headers=headers, json=payload)
                if r.status_code != 200:
                    logger.error(f"Failed to send WhatsApp message: {r.text}")
                    
        except Exception as e:
            logger.error(f"WhatsApp processing error: {e}")


async def process_instagram_message(agent_id, sender_id, text, token):
    from app.services.scheduler import AgentAutonomousEngine
    from app.core.database import async_session_maker
    
    async with async_session_maker() as db:
        stmt = select(CustomAgent).where(CustomAgent.id == agent_id)
        res = await db.execute(stmt)
        agent = res.scalar_one_or_none()
        
        if not agent:
            return
            
        try:
            result = await AgentAutonomousEngine.run_agent(
                agent=agent,
                input_text=text,
                trigger_type="INSTAGRAM",
                db=db,
                telegram_chat_id=None
            )
            ai_reply = result.get("response", "Üzgünüm, şu an yanıt veremiyorum.")
            
            # Send HTTP back to Instagram Graph API
            url = f"https://graph.facebook.com/v19.0/me/messages?access_token={token}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "recipient": {"id": sender_id},
                "message": {"text": ai_reply}
            }
            
            async with httpx.AsyncClient() as client:
                r = await client.post(url, headers=headers, json=payload)
                if r.status_code != 200:
                    logger.error(f"Failed to send Instagram message: {r.text}")
                    
        except Exception as e:
            logger.error(f"Instagram processing error: {e}")
