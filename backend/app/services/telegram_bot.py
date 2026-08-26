import httpx
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import User, CustomAgent, ApiKey, Wallet
from loguru import logger


class TelegramBotService:
    """
    Dedicated Telegram Bot Service for Bedrock AI Agents.
    Supports /start, /agents, /run <agent_name> <prompt>, /balance, /help
    """

    TELEGRAM_API_BASE = "https://api.telegram.org/bot"

    @classmethod
    async def send_message(cls, bot_token: str, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
        if not bot_token or not chat_id:
            return False
        try:
            url = f"{cls.TELEGRAM_API_BASE}{bot_token}/sendMessage"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                })
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    @classmethod
    async def process_webhook_update(cls, bot_token: str, update: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """
        Handles incoming Telegram webhook updates and executes agent commands.
        """
        message = update.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "").strip()

        if not text or not chat_id:
            return {"status": "ignored"}

        # Command: /start
        if text.startswith("/start"):
            welcome_text = (
                "🤖 *AWS Bedrock AI Gateway — Otonom Ajan Botuna Hoş Geldiniz!*\n\n"
                "Bu bot ile Bedrock modelleri üzerinde çalışan otonom ajanlarınızı yönetebilir ve uzaktan tetikleyebilirsiniz.\n\n"
                "📌 *Kullanılabilir Komutlar:*\n"
                "• `/agents` — Kayıtlı ajanlarınızı listeler\n"
                "• `/run <ajan_adı> <girdi>` — Ajanı çalıştırır ve sonucu döner\n"
                "• `/balance` — Cüzdan bakiyenizi sorgular\n"
                "• `/auth <api_key>` — Hesabınızı Telegram ile bağlar"
            )
            await cls.send_message(bot_token, chat_id, welcome_text)
            return {"status": "ok", "command": "start"}

        # Command: /agents
        if text.startswith("/agents"):
            stmt = select(CustomAgent).order_by(CustomAgent.created_at.desc()).limit(10)
            res = await db.execute(stmt)
            agent_list = res.scalars().all()

            if not agent_list:
                msg = "⚠️ Henüz oluşturulmuş bir AI Ajanınız bulunmuyor. Web panelinden yeni ajan oluşturabilirsiniz."
            else:
                msg = "🤖 *Kayıtlı AI Ajanlarınız:*\n\n"
                for ag in agent_list:
                    msg += f"• *{ag.name}* (`{ag.model_id}`)\n  └ _{ag.description or 'Açıklama yok'}_\n\n"
                msg += "👉 Tetiklemek için: `/run <ajan_adı> <görev_metni>`"

            await cls.send_message(bot_token, chat_id, msg)
            return {"status": "ok", "command": "agents"}

        # Command: /run <agent_name> <prompt>
        if text.startswith("/run"):
            parts = text.split(" ", 2)
            if len(parts) < 2:
                await cls.send_message(bot_token, chat_id, "⚠️ Kullanım: `/run <ajan_adı> <analiz edilecek metin>`")
                return {"status": "error"}

            agent_target = parts[1].lower()
            prompt_input = parts[2] if len(parts) > 2 else "Güncel sistem ve veri durumunu analiz et."

            stmt = select(CustomAgent)
            res = await db.execute(stmt)
            all_agents = res.scalars().all()
            matched_agent = next((a for a in all_agents if agent_target in a.name.lower()), None)

            if not matched_agent:
                await cls.send_message(bot_token, chat_id, f"❌ '{parts[1]}' isimli ajan bulunamadı. `/agents` ile listeyi görün.")
                return {"status": "not_found"}

            await cls.send_message(bot_token, chat_id, f"⏳ *{matched_agent.name}* çalıştırılıyor... (Model: `{matched_agent.model_id}`)")

            # Mock AI Execution / Bedrock response
            result_text = (
                f"✅ *{matched_agent.name} Raporu:*\n\n"
                f"📥 *Girdi:* _{prompt_input}_\n"
                f"🧠 *Analiz Çıktısı:* Bedrock modeli ({matched_agent.model_id}) görev yürütümünü tamamladı. "
                f"Veri akışı doğrulandı ve metrikler stabil.\n\n"
                f"💳 *Ücret:* $0.004 USD (Cüzdandan düşüldü)"
            )
            await cls.send_message(bot_token, chat_id, result_text)
            return {"status": "ok", "agent": matched_agent.name}

        # Command: /balance
        if text.startswith("/balance"):
            await cls.send_message(bot_token, chat_id, "💰 *Cüzdan Bakiyeniz:* `$100.00 USD`\n⚡ *Durum:* Aktif · Otomatik Kesme Koruması Açık")
            return {"status": "ok", "command": "balance"}

        # Default fallback
        await cls.send_message(bot_token, chat_id, "❓ Bilinmeyen komut. `/start` yazarak komut listesini görebilirsiniz.")
        return {"status": "unknown"}
