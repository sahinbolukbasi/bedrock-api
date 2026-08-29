import os
import base64
import httpx
import io

import random
import re
import string
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.entities import User, CustomAgent, Wallet, AgentExecutionLog, ScheduledTask, ModelCatalog
from app.services.web_search import WebSearchService
from app.services.scheduler import parse_time_expression, parse_interval_expression, AgentAutonomousEngine
from app.domain.schemas import ImageGenerationRequest
from app.providers.router import provider_router
from app.core.metrics import TELEGRAM_MESSAGES_TOTAL
from loguru import logger
import asyncio

from app.core.config import settings
from app.core.secrets_manager import AWSSecretsManagerService


def get_telegram_bot_token() -> Optional[str]:
    """Dynamically resolves the active Telegram bot token with zero static fallback leaks."""
    return os.getenv("TELEGRAM_BOT_TOKEN") or settings.TELEGRAM_BOT_TOKEN or AWSSecretsManagerService.get_secret("TELEGRAM_BOT_TOKEN")


def get_telegram_bot_username() -> str:
    """Dynamically resolves the Telegram bot username."""
    return os.getenv("TELEGRAM_BOT_USERNAME") or settings.TELEGRAM_BOT_USERNAME or AWSSecretsManagerService.get_secret("TELEGRAM_BOT_USERNAME", default="BedrocksAiBot")







def get_main_menu_keyboard() -> Dict[str, Any]:
    """Returns interactive inline keyboard for fast actions."""
    return {
        "inline_keyboard": [
            [
                {"text": "🤖 Botlarım & Ajanlar", "callback_data": "menu:agents"},
                {"text": "➕ Yeni Bot Oluştur", "callback_data": "menu:newbot"}
            ],
            [
                {"text": "⏰ Hatırlatıcılar", "callback_data": "menu:reminders"},
                {"text": "🌐 Web & Haber Takibi", "callback_data": "menu:tracks"}
            ],
            [
                {"text": "🎨 Görsel Üret (Image)", "callback_data": "menu:image"},
                {"text": "💳 Cüzdan & Bakiye", "callback_data": "menu:balance"}
            ]
        ]
    }


class TelegramBotService:
    """
    Production Hybrid Telegram Bot Service for Bedrock AI Gateway.
    - Zero-latency Deterministic Routing: Timers, Reminders, Interval Trackers, Bot Switcher, Status.
    - LLM & Autonomous Agent Routing: Complex reasoning, web synthesis, conversational agents.
    - Media generation: AWS Bedrock Titan Image Generator with Telegram sendPhoto.
    """

    TELEGRAM_API_BASE = "https://api.telegram.org/bot"

    @classmethod
    async def send_message(
        cls, 
        bot_token: Optional[str], 
        chat_id: str, 
        text: str, 
        parse_mode: str = "Markdown",
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        token = bot_token or get_telegram_bot_token()
        if not token or not chat_id or not text:
            return False
        try:
            url = f"{cls.TELEGRAM_API_BASE}{token}/sendMessage"
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                for idx, chunk in enumerate(chunks):
                    payload: Dict[str, Any] = {
                        "chat_id": chat_id,
                        "text": chunk,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": False
                    }
                    if idx == len(chunks) - 1 and reply_markup:
                        payload["reply_markup"] = reply_markup

                    resp = await client.post(url, json=payload)
                    if resp.status_code != 200:
                        # Fallback without Markdown
                        payload.pop("parse_mode", None)
                        await client.post(url, json=payload)
                try:
                    TELEGRAM_MESSAGES_TOTAL.labels(direction="outgoing").inc()
                except Exception:
                    pass
                return True
        except Exception as e:
            logger.error(f"[TelegramBotService] Failed to send message to {chat_id}: {e}")
            return False


    @classmethod
    async def send_photo(
        cls,
        bot_token: Optional[str],
        chat_id: str,
        photo: str,  # URL or base64 data
        caption: Optional[str] = None,
        parse_mode: str = "Markdown",
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        token = bot_token or get_telegram_bot_token()
        if not token or not chat_id or not photo:
            return False
        try:
            url = f"{cls.TELEGRAM_API_BASE}{token}/sendPhoto"
            async with httpx.AsyncClient(timeout=30.0) as client:
                if photo.startswith("http://") or photo.startswith("https://"):
                    payload: Dict[str, Any] = {
                        "chat_id": chat_id,
                        "photo": photo,
                        "caption": caption[:1024] if caption else None,
                        "parse_mode": parse_mode
                    }
                    if reply_markup:
                        payload["reply_markup"] = reply_markup
                    resp = await client.post(url, json=payload)
                    return resp.status_code == 200
                else:
                    # Treat as base64 image file upload
                    clean_b64 = photo.split(",")[-1].strip()
                    image_bytes = base64.b64decode(clean_b64)
                    files = {"photo": ("image.png", image_bytes, "image/png")}
                    data: Dict[str, Any] = {"chat_id": chat_id}
                    if caption:
                        data["caption"] = caption[:1024]
                        data["parse_mode"] = parse_mode
                    resp = await client.post(url, data=data, files=files)
                    return resp.status_code == 200
        except Exception as e:
            logger.error(f"[TelegramBotService] Failed to send photo to {chat_id}: {e}")
            return False

    @classmethod
    async def answer_callback_query(
        cls,
        bot_token: Optional[str],
        callback_query_id: str,
        text: Optional[str] = None
    ) -> bool:
        token = bot_token or get_telegram_bot_token()
        try:
            url = f"{cls.TELEGRAM_API_BASE}{token}/answerCallbackQuery"
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json={"callback_query_id": callback_query_id, "text": text or ""})
                return True
        except Exception as e:
            logger.error(f"[TelegramBotService] Callback query answer error: {e}")
            return False

    @classmethod
    async def generate_pairing_code(cls, user_id: Any, db: AsyncSession) -> str:
        code_digits = "".join(random.choices(string.digits, k=6))
        code = f"TG-{code_digits}"
        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            user.telegram_pairing_code = code
            await db.commit()
        return code

    @classmethod
    async def pair_user_by_code(
        cls, 
        pairing_code: str, 
        chat_id: str, 
        username: Optional[str], 
        db: AsyncSession
    ) -> Optional[User]:
        clean_code = pairing_code.strip().upper()
        clean_code = re.sub(r"^(?:/START|/PAIR|\?START=|=)\s*", "", clean_code).strip()

        search_codes = [clean_code]
        if clean_code.startswith("TG-"):
            search_codes.append(clean_code.replace("TG-", ""))
        elif len(clean_code) == 6:
            search_codes.append(f"TG-{clean_code}")

        stmt = select(User).where(User.telegram_pairing_code.in_(search_codes))
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if user:
            user.telegram_chat_id = str(chat_id)
            user.telegram_username = username or ""
            user.telegram_pairing_code = None
            await db.commit()
            await db.refresh(user)
            logger.info(f"[TelegramBotService] Successfully paired user {user.email} with Telegram chat_id {chat_id}")
            return user
        return None

    @classmethod
    async def process_webhook_update(
        cls, 
        bot_token: str, 
        update_data: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        token = bot_token or get_telegram_bot_token()
        try:
            TELEGRAM_MESSAGES_TOTAL.labels(direction="incoming").inc()
        except Exception:
            pass

        # -------------------------------------------------------------
        # Handle Callback Queries (Inline Button Clicks)
        # -------------------------------------------------------------
        if "callback_query" in update_data:

            cq = update_data["callback_query"]
            cq_id = cq["id"]
            chat_id = str(cq.get("message", {}).get("chat", {}).get("id", ""))
            data = cq.get("data", "")
            await cls.answer_callback_query(token, cq_id)

            user_stmt = select(User).where(User.telegram_chat_id == chat_id)
            u_res = await db.execute(user_stmt)
            user = u_res.scalar_one_or_none()

            if not user:
                await cls.send_message(token, chat_id, "🔒 Lütfen önce `/pair TG-XXXXXX` ile hesabınızı bağlayın.")
                return {"status": "unauthorized"}

            if data == "menu:agents":
                return await cls._handle_agents_command(token, chat_id, user, db)
            elif data == "menu:newbot":
                help_new = (
                    "➕ *Yeni Otonom Bot Oluşturma:*\n\n"
                    "Aşağıdaki formatta komut göndererek anında yeni bir bot tanımlayabilirsiniz:\n\n"
                    "`/newbot <Bot Adı> | <Rol & Talimatlar> | <Web:Evet/Hayır> | <Model>`\n\n"
                    "📌 *Örnek:*\n"
                    "`/newbot Kripto Uzmanı | Kripto para piyasasını analiz edip tavsiyeler sun. | evet | amazon.nova-micro-v1:0`"
                )
                await cls.send_message(token, chat_id, help_new)
                return {"status": "ok", "action": "newbot_help"}
            elif data == "menu:reminders":
                return await cls._handle_list_reminders(token, chat_id, user, db)
            elif data == "menu:tracks":
                return await cls._handle_list_tracks(token, chat_id, user, db)
            elif data == "menu:image":
                help_img = (
                    "🎨 *Görsel (Image) Üretimi:*\n\n"
                    "AWS Bedrock Titan Image Generator ile istediğiniz resmi oluşturabilirsiniz.\n\n"
                    "📌 *Kullanım:* `/image <görsel açıklaması>`\n"
                    "👉 *Örnek:* `/image Boğaz köprüsü üzerinde siberpunk uçan arabalar, 4k ultra detay`"
                )
                await cls.send_message(token, chat_id, help_img)
                return {"status": "ok", "action": "image_help"}
            elif data == "menu:balance":
                return await cls._handle_balance_command(token, chat_id, user, db)
            elif data.startswith("cb:switch:"):
                agent_id_str = data.split("cb:switch:")[1]
                return await cls._switch_agent(token, chat_id, agent_id_str, user, db)
            elif data.startswith("cb:cancel:"):
                task_id_str = data.split("cb:cancel:")[1]
                return await cls._cancel_task(token, chat_id, task_id_str, user, db)

            return {"status": "ok", "callback": data}

        # -------------------------------------------------------------
        # Handle Regular Messages
        # -------------------------------------------------------------
        message = update_data.get("message") or update_data.get("edited_message")
        if not message or "text" not in message:
            return {"status": "ignored"}

        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        username = chat.get("username", "") or message.get("from", {}).get("first_name", "")
        text = message.get("text", "").strip()

        if not text or not chat_id:
            return {"status": "ignored"}

        # Find user if paired
        user_stmt = select(User).where(User.telegram_chat_id == chat_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        # Command: /start [param] or /help or /menu
        if text.startswith("/start") or text.startswith("/help") or text.startswith("/menu"):
            parts = text.split(" ", 1)
            if len(parts) > 1 and parts[1].strip():
                param = parts[1].strip()
                paired_user = await cls.pair_user_by_code(param, chat_id, username, db)
                if paired_user:
                    welcome_text = (
                        f"🎉 *Tebrikler! AWS Bedrock AI Hesabınız Başarıyla Eşleşti!*\n\n"
                        f"👤 *Kullanıcı:* `{paired_user.email}`\n"
                        f"🆔 *Telegram Chat ID:* `{chat_id}`\n\n"
                        f"⚡ *Hızlı İşlemler İçin Menüyü Kullanabilirsiniz:*"
                    )
                    await cls.send_message(token, chat_id, welcome_text, reply_markup=get_main_menu_keyboard())
                    return {"status": "paired", "user": paired_user.email}

            if user:
                msg = (
                    f"🤖 *AWS Bedrock AI — Hibrit Ajan & Otomasyon Asistanı*\n\n"
                    f"Hoş geldiniz, *{user.full_name or user.email}*!\n\n"
                    f"⚡ *Özellikler & Hızlı Komutlar:*\n"
                    f"• `/remind 10m Toplantı` — Zilli hatırlatıcı kurar.\n"
                    f"• `/track 1h Yapay Zeka` — Belirli aralıklarla canlı web taraması yapar.\n"
                    f"• `/image <prompt>` — AWS Titan ile fotoğraf üretip gönderir.\n"
                    f"• `/agents` veya `/switch` — Özel botlarınızı seçip yönetin.\n"
                    f"• `/haber <konu>` — Anlık canlı haber ve web taraması."
                )
                await cls.send_message(token, chat_id, msg, reply_markup=get_main_menu_keyboard())
            else:
                msg = (
                    "👋 *AWS Bedrock AI Gateway Botuna Hoş Geldiniz!*\n\n"
                    "Otonom AI ajanlarınızı yönetmek, hatırlatıcı kurmak, web takipçisi başlatmak ve görsel üretmek için hesabınızı bağlayın:\n\n"
                    "👉 `/pair TG-XXXXXX` (Web panelindeki eşleştirme kodunuzu girin)"
                )
                await cls.send_message(token, chat_id, msg)
            return {"status": "ok", "command": "start"}

        # Command: /pair <code>
        if text.startswith("/pair"):
            parts = text.split(" ", 1)
            if len(parts) < 2:
                await cls.send_message(token, chat_id, "⚠️ Lütfen eşleştirme kodunu girin: `/pair TG-123456`")
                return {"status": "missing_code"}
            code = parts[1].strip()
            paired_user = await cls.pair_user_by_code(code, chat_id, username, db)
            if paired_user:
                await cls.send_message(
                    token, 
                    chat_id, 
                    f"✅ *Hesabınız Başarıyla Bağlandı!*\n\n👤 *Kullanıcı:* `{paired_user.email}`",
                    reply_markup=get_main_menu_keyboard()
                )
                return {"status": "paired"}
            else:
                await cls.send_message(token, chat_id, "❌ *Eşleştirme Başarısız.* Kod hatalı veya süresi dolmuş.")
                return {"status": "invalid_code"}

        # Direct pairing code entered without /pair
        if not user and (text.upper().startswith("TG-") or (len(text.strip()) == 6 and text.strip().isdigit())):
            paired_user = await cls.pair_user_by_code(text, chat_id, username, db)
            if paired_user:
                welcome_text = (
                    f"🎉 *Tebrikler! AWS Bedrock AI Hesabınız Başarıyla Eşleşti!*\n\n"
                    f"👤 *Kullanıcı:* `{paired_user.email}`\n"
                    f"🆔 *Telegram Chat ID:* `{chat_id}`\n\n"
                    f"⚡ *Hızlı İşlemler İçin Menüyü Kullanabilirsiniz:*"
                )
                await cls.send_message(token, chat_id, welcome_text, reply_markup=get_main_menu_keyboard())
                return {"status": "paired", "user": paired_user.email}

        if not user:
            await cls.send_message(
                token, 
                chat_id, 
                "🔒 *Yetkilendirme Gerekli:*\nLütfen önce hesabınızı bağlayın: `/pair TG-XXXXXX`"
            )
            return {"status": "unauthorized"}

        # -------------------------------------------------------------
        # DETERMINISTIC FAST ROUTING (No LLM Cost / Instant Execution)
        # -------------------------------------------------------------

        # 1. Reminders: /remind <time> <message>
        if text.startswith("/remind") or text.startswith("/hatirlat"):
            return await cls._handle_create_reminder(token, chat_id, text, user, db)

        # 2. List Reminders: /reminders or /hatirlaticilar
        if text.startswith("/reminders") or text.startswith("/hatirlaticilar"):
            return await cls._handle_list_reminders(token, chat_id, user, db)

        # 3. Recurring Web Search Tracker: /track <interval> <query> or /takip
        if text.startswith("/track") or text.startswith("/takip"):
            return await cls._handle_create_track(token, chat_id, text, user, db)

        # 4. List Tracks: /tracks or /takipler
        if text.startswith("/tracks") or text.startswith("/takipler"):
            return await cls._handle_list_tracks(token, chat_id, user, db)

        # 5. Cancel Scheduled Task: /cancel <task_id> or /iptal
        if text.startswith("/cancel") or text.startswith("/iptal"):
            parts = text.split(" ", 1)
            task_arg = parts[1].strip() if len(parts) > 1 else ""
            return await cls._cancel_task(token, chat_id, task_arg, user, db)

        # 6. Image Generation: /image <prompt> or /gorsel or /ciz
        if text.startswith("/image") or text.startswith("/gorsel") or text.startswith("/ciz"):
            parts = text.split(" ", 1)
            prompt = parts[1].strip() if len(parts) > 1 else ""
            return await cls._handle_image_generation(token, chat_id, prompt, user, db)

        # 7. Create New Bot: /newbot <name> | <system_prompt> | <web_search:yes/no> | <model>
        if text.startswith("/newbot") or text.startswith("/yenibot"):
            return await cls._handle_create_bot(token, chat_id, text, user, db)

        # 8. List Bots: /agents or /botlar
        if text.startswith("/agents") or text.startswith("/botlar"):
            return await cls._handle_agents_command(token, chat_id, user, db)

        # 9. Switch Bot: /switch <bot_name_or_id>
        if text.startswith("/switch"):
            parts = text.split(" ", 1)
            target = parts[1].strip() if len(parts) > 1 else ""
            return await cls._switch_agent(token, chat_id, target, user, db)

        # 10. Balance: /balance or /bakiye
        if text.startswith("/balance") or text.startswith("/bakiye"):
            return await cls._handle_balance_command(token, chat_id, user, db)

        # -------------------------------------------------------------
        # HYBRID SMART INTENT DETECTION (Natural Language Fast Paths)
        # -------------------------------------------------------------
        # A. Smart Natural Reminder: e.g. "10 dakika sonra bana su içmeyi hatırlat"
        nl_remind = re.match(r"^(\d+\s*(?:saniye|dakika|dk|saat|gün|s|m|h|d))\s+sonra\s+(.+)", text, re.IGNORECASE)
        if nl_remind:
            time_part = nl_remind.group(1)
            content_part = nl_remind.group(2)
            simulated_cmd = f"/remind {time_part} {content_part}"
            return await cls._handle_create_reminder(token, chat_id, simulated_cmd, user, db)

        # B. Smart Image Request: e.g. "görsel oluştur: deniz kenarı"
        if text.lower().startswith("görsel oluştur:") or text.lower().startswith("resim çiz:"):
            img_p = text.split(":", 1)[1].strip()
            return await cls._handle_image_generation(token, chat_id, img_p, user, db)

        # -------------------------------------------------------------
        # LLM AGENT ROUTING (Autonomous Reasoning, Web Search & Tools)
        # -------------------------------------------------------------
        return await cls._route_to_active_agent(token, chat_id, text, user, db)

    # -----------------------------------------------------------------
    # SUB-HANDLERS (Deterministic & Modular)
    # -----------------------------------------------------------------

    @classmethod
    async def _handle_create_reminder(cls, token: str, chat_id: str, text: str, user: User, db: AsyncSession) -> Dict[str, Any]:
        remind_pattern = re.match(
            r"^(?:/remind|/hatirlat)\s+(\d+\s*(?:s|sec|secs|saniye|m|min|mins|dakika|dk|h|hr|hrs|saat|d|day|days|gun|gün)|\d{1,2}:\d{2})\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if remind_pattern:
            time_str = remind_pattern.group(1).strip()
            remind_content = remind_pattern.group(2).strip()
        else:
            parts = text.split(" ", 2)
            if len(parts) < 3:
                await cls.send_message(
                    token, 
                    chat_id, 
                    "⚠️ *Kullanım:* `/remind <süre/saat> <mesaj>`\n\n👉 *Örnekler:*\n• `/remind 10m Kahve molası ver`\n• `/remind 2h Müşteri toplantısı`\n• `/remind 17:30 Günlük raporu gönder`"
                )
                return {"status": "invalid_args"}
            time_str = parts[1].strip()
            remind_content = parts[2].strip()

        due_time = parse_time_expression(time_str)
        if not due_time:
            await cls.send_message(token, chat_id, f"❌ *Geçersiz zaman formatı:* `{time_str}`\n`10s`, `15m`, `2h`, `1d` veya `15:30` gibi formatlar kullanın.")
            return {"status": "invalid_time"}


        task = ScheduledTask(
            user_id=user.id,
            task_type="REMINDER",
            title=remind_content,
            payload={"chat_id": chat_id, "prompt": remind_content},
            schedule_type="ONCE",
            next_run_at=due_time,
            status="ACTIVE"
        )
        db.add(task)
        await db.commit()

        delta_sec = int((due_time - datetime.now(timezone.utc)).total_seconds())
        delta_str = f"{delta_sec // 60} dakika sonra" if delta_sec >= 60 else f"{delta_sec} saniye sonra"
        formatted_due = due_time.strftime("%H:%M:%S UTC")

        confirm_msg = (
            f"⏰ *Hatırlatıcı Başarıyla Kuruldu!* 🔔\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 *Konu:* {remind_content}\n"
            f"⏳ *Zaman:* {formatted_due} (_{delta_str}_)\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🗑️ İptal etmek için: `/cancel {str(task.id)[:8]}`"
        )
        await cls.send_message(token, chat_id, confirm_msg)
        return {"status": "ok", "task_id": str(task.id)}

    @classmethod
    async def _handle_list_reminders(cls, token: str, chat_id: str, user: User, db: AsyncSession) -> Dict[str, Any]:
        stmt = select(ScheduledTask).where(
            ScheduledTask.user_id == user.id,
            ScheduledTask.task_type == "REMINDER",
            ScheduledTask.status == "ACTIVE"
        ).order_by(ScheduledTask.next_run_at.asc())
        res = await db.execute(stmt)
        reminders = res.scalars().all()

        if not reminders:
            await cls.send_message(token, chat_id, "⏰ *Aktif bir hatırlatıcınız bulunmuyor.*\nKurmak için: `/remind 15m Toplantı`")
            return {"status": "ok", "count": 0}

        msg = f"⏰ *Aktif Hatırlatıcılarınız ({len(reminders)} adet):*\n\n"
        buttons = []
        for r in reminders:
            due_str = r.next_run_at.strftime("%H:%M:%S UTC")
            msg += f"• 🔔 *{r.title}*\n  └ ⏳ Zaman: `{due_str}` (ID: `{str(r.id)[:8]}`)\n\n"
            buttons.append([{"text": f"❌ İptal: {r.title[:20]}", "callback_data": f"cb:cancel:{str(r.id)}"}])

        await cls.send_message(token, chat_id, msg, reply_markup={"inline_keyboard": buttons})
        return {"status": "ok", "count": len(reminders)}

    @classmethod
    async def _handle_create_track(cls, token: str, chat_id: str, text: str, user: User, db: AsyncSession) -> Dict[str, Any]:
        parts = text.split(" ", 2)
        if len(parts) < 3:
            await cls.send_message(
                token, 
                chat_id, 
                "⚠️ *Kullanım:* `/track <aralık> <konu>`\n\n👉 *Örnekler:*\n• `/track 1h Yapay Zeka ve LLM Gelişmeleri`\n• `/track 30m Borsa İstanbul Son Durum`\n• `/track 6h Bitcoin ve Kripto Para`"
            )
            return {"status": "invalid_args"}

        interval_str = parts[1].strip()
        query = parts[2].strip()

        interval_sec = parse_interval_expression(interval_str)
        if not interval_sec:
            await cls.send_message(token, chat_id, f"❌ *Geçersiz aralık:* `{interval_str}`. Örnek: `30m`, `1h`, `6h`, `1d`")
            return {"status": "invalid_interval"}

        now = datetime.now(timezone.utc)
        task = ScheduledTask(
            user_id=user.id,
            task_type="WEB_SEARCH_TRACKER",
            title=f"Web Takip: {query}",
            payload={"chat_id": chat_id, "search_query": query},
            schedule_type="INTERVAL",
            interval_seconds=interval_sec,
            next_run_at=now + timedelta(seconds=interval_sec),
            status="ACTIVE"
        )
        db.add(task)
        await db.commit()

        msg = (
            f"🌐 *Otomatik Web Takipçisi Başlatıldı!* 📡\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Takip Konusu:* `{query}`\n"
            f"🔄 *Periyot:* Her `{interval_str}`\n"
            f"⏰ *İlk Tarama:* {(now + timedelta(seconds=interval_sec)).strftime('%H:%M:%S UTC')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Belirtilen aralıkta yeni haber ve web içerikleri otomatik taranıp buraya iletilecektir.\n"
            f"🗑️ İptal: `/cancel {str(task.id)[:8]}`"
        )
        await cls.send_message(token, chat_id, msg)
        return {"status": "ok", "task_id": str(task.id)}

    @classmethod
    async def _handle_list_tracks(cls, token: str, chat_id: str, user: User, db: AsyncSession) -> Dict[str, Any]:
        stmt = select(ScheduledTask).where(
            ScheduledTask.user_id == user.id,
            ScheduledTask.task_type == "WEB_SEARCH_TRACKER",
            ScheduledTask.status == "ACTIVE"
        ).order_by(ScheduledTask.created_at.desc())
        res = await db.execute(stmt)
        tracks = res.scalars().all()

        if not tracks:
            await cls.send_message(token, chat_id, "🌐 *Aktif bir web takipçiniz bulunmuyor.*\nBaşlatmak için: `/track 1h Yapay Zeka Haberleri`")
            return {"status": "ok", "count": 0}

        msg = f"🌐 *Aktif Web & Haber Takipçileriniz ({len(tracks)} adet):*\n\n"
        buttons = []
        for t in tracks:
            query = t.payload.get("search_query") or t.title
            interval_min = (t.interval_seconds or 3600) // 60
            msg += f"• 📡 *{query}*\n  └ 🔄 Aralık: `{interval_min} dakika` · Toplam Tarama: `{t.run_count}`\n\n"
            buttons.append([{"text": f"❌ Takibi Durdur: {query[:20]}", "callback_data": f"cb:cancel:{str(t.id)}"}])

        await cls.send_message(token, chat_id, msg, reply_markup={"inline_keyboard": buttons})
        return {"status": "ok", "count": len(tracks)}

    @classmethod
    async def _cancel_task(cls, token: str, chat_id: str, task_arg: str, user: User, db: AsyncSession) -> Dict[str, Any]:
        if not task_arg:
            await cls.send_message(token, chat_id, "⚠️ İptal etmek istediğiniz görevin ID'sini belirtin: `/cancel <id>`")
            return {"status": "missing_id"}

        # Match exact UUID or prefix
        stmt = select(ScheduledTask).where(ScheduledTask.user_id == user.id, ScheduledTask.status == "ACTIVE")
        res = await db.execute(stmt)
        tasks = res.scalars().all()

        target_task = None
        for t in tasks:
            if str(t.id).startswith(task_arg.lower()) or str(t.id) == task_arg:
                target_task = t
                break

        if not target_task:
            await cls.send_message(token, chat_id, f"❌ `{task_arg}` ID'li aktif bir görev bulunamadı.")
            return {"status": "not_found"}

        target_task.status = "CANCELLED"
        await db.commit()
        await cls.send_message(token, chat_id, f"✅ *Görev İptal Edildi:* `{target_task.title}`")
        return {"status": "ok", "cancelled": str(target_task.id)}

    @classmethod
    async def _handle_image_generation(cls, token: str, chat_id: str, prompt: str, user: User, db: AsyncSession) -> Dict[str, Any]:
        if not prompt:
            await cls.send_message(token, chat_id, "⚠️ *Kullanım:* `/image <görsel açıklaması>`\nÖrn: `/image Siberpunk İstanbul manzarası, neon ışıklar`")
            return {"status": "missing_prompt"}

        await cls.send_message(token, chat_id, f"🎨 *AWS Bedrock Titan Image Generator çalışıyor...*\n_İstem:_ `{prompt}`")

        provider = provider_router.get_provider("BEDROCK")
        dummy_image_model = ModelCatalog(
            model_id="amazon.titan-image-generator-v2:0",
            name="titan-image-generator-v2",
            display_name="Amazon Titan Image Generator G1 v2",
            provider="BEDROCK",
            type="IMAGE"
        )

        req = ImageGenerationRequest(
            prompt=prompt,
            model="amazon.titan-image-generator-v2:0",
            n=1,
            size="1024x1024"
        )

        try:
            resp = await provider.generate_image(req, dummy_image_model)
            if resp.data and len(resp.data) > 0:
                first_img = resp.data[0]
                img_src = first_img.url or first_img.b64_json or ""
                caption = f"🎨 *AWS Titan Image Çıktısı*\n📌 *İstem:* _{prompt}_\n⚡ _Model: amazon.titan-image-generator-v2:0_"
                
                success = await cls.send_photo(token, chat_id, img_src, caption=caption)
                if not success:
                    # Fallback to URL link message
                    await cls.send_message(token, chat_id, f"{caption}\n\n🖼️ [Görseli Aç]({img_src})")
                return {"status": "ok", "image_generated": True}
        except Exception as e:
            logger.error(f"[TelegramBotService] Image gen error: {e}")
            await cls.send_message(token, chat_id, f"⚠️ Görsel üretimi sırasında hata oluştu: {e}")
        return {"status": "error"}

    @classmethod
    async def _handle_create_bot(cls, token: str, chat_id: str, text: str, user: User, db: AsyncSession) -> Dict[str, Any]:
        parts = text.split(" ", 1)
        if len(parts) < 2 or "|" not in parts[1]:
            help_msg = (
                "⚠️ *Format:* `/newbot <İsim> | <Rol & Talimatlar> | <Web:Evet/Hayır> | <Model>`\n\n"
                "👉 *Örnek:*\n"
                "`/newbot Finans Danışmanı | Borsa ve altın analizleri yap | evet | amazon.nova-micro-v1:0`"
            )
            await cls.send_message(token, chat_id, help_msg)
            return {"status": "invalid_format"}

        segments = [s.strip() for s in parts[1].split("|")]
        name = segments[0] if len(segments) > 0 else "Özel Bot"
        prompt = segments[1] if len(segments) > 1 else "Sen faydalı bir AI asistanısın."
        web_search = True if len(segments) > 2 and segments[2].lower() in ("evet", "yes", "true", "1") else False
        model_id = segments[3] if len(segments) > 3 and segments[3] else "amazon.nova-micro-v1:0"

        new_agent = CustomAgent(
            user_id=user.id,
            name=name,
            icon="🤖",
            agent_type="custom",
            model_id=model_id,
            system_prompt=prompt,
            tools_config={"web_search": web_search, "telegram": True}
        )
        db.add(new_agent)
        await db.flush()

        user.telegram_active_agent_id = new_agent.id
        await db.commit()

        msg = (
            f"🎉 *Yeni Otonom Bot Başarıyla Oluşturuldu!* 🤖\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📛 *İsim:* {new_agent.name}\n"
            f"🧠 *Model:* `{model_id}`\n"
            f"🌐 *Canlı Web Arama:* {'Aktif ✅' if web_search else 'Pasif ❌'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ Bu bot şu an *aktif botunuz* olarak seçildi! Buraya doğrudan mesaj yazdığınızda bu bot yanıt verecektir."
        )
        await cls.send_message(token, chat_id, msg)
        return {"status": "ok", "agent_id": str(new_agent.id)}

    @classmethod
    async def _handle_agents_command(cls, token: str, chat_id: str, user: User, db: AsyncSession) -> Dict[str, Any]:
        stmt = select(CustomAgent).where(CustomAgent.user_id == user.id).order_by(CustomAgent.created_at.desc())
        res = await db.execute(stmt)
        agents = res.scalars().all()

        if not agents:
            msg = (
                "🤖 *Tanımlı Özel Botunuz Bulunmuyor.*\n\n"
                "Hemen oluşturmak için:\n"
                "`/newbot <İsim> | <Rol> | <Web:Evet/Hayır> | <Model>`"
            )
            await cls.send_message(token, chat_id, msg)
            return {"status": "ok", "count": 0}

        active_id = user.telegram_active_agent_id
        msg = f"🤖 *Kayıtlı Otonom Botlarınız ({len(agents)} adet):*\n\n"
        buttons = []

        for ag in agents:
            is_active = (ag.id == active_id)
            status_tag = "⭐ (AKTİF)" if is_active else ""
            tools = ag.tools_config or {}
            has_web = "🌐 Web" if tools.get("web_search") else ""
            
            msg += f"• {ag.icon} *{ag.name}* {status_tag}\n"
            msg += f"  └ Model: `{ag.model_id}` {f'· {has_web}' if has_web else ''}\n\n"
            
            btn_text = f"{'✅' if is_active else '👉'} {ag.name}"
            buttons.append([{"text": btn_text, "callback_data": f"cb:switch:{str(ag.id)}"}])

        msg += "Bir botla sohbet etmek için aşağıdaki listeden seçin veya `/switch <bot_adı>` yazın."
        await cls.send_message(token, chat_id, msg, reply_markup={"inline_keyboard": buttons})
        return {"status": "ok", "count": len(agents)}

    @classmethod
    async def _switch_agent(cls, token: str, chat_id: str, target: str, user: User, db: AsyncSession) -> Dict[str, Any]:
        if not target:
            await cls.send_message(token, chat_id, "⚠️ Geçiş yapmak istediğiniz botu belirtin: `/switch <bot_adı>`")
            return {"status": "missing_target"}

        stmt = select(CustomAgent).where(CustomAgent.user_id == user.id)
        res = await db.execute(stmt)
        agents = res.scalars().all()

        selected = None
        for ag in agents:
            if str(ag.id) == target or ag.name.lower() == target.lower() or target.lower() in ag.name.lower():
                selected = ag
                break

        if not selected:
            await cls.send_message(token, chat_id, f"❌ `{target}` adında bir bot bulunamadı. Listeyi görmek için: `/agents`")
            return {"status": "not_found"}

        user.telegram_active_agent_id = selected.id
        await db.commit()

        msg = (
            f"✅ *Aktif Bot Değiştirildi!* 🔄\n\n"
            f"Şu an konuşulan bot: {selected.icon} *{selected.name}*\n"
            f"🧠 _Model: {selected.model_id}_\n"
            f"📜 _Rol: {selected.system_prompt[:120]}..._\n\n"
            f"Artık doğrudan yazdığınız mesajlar bu bot tarafından yanıtlanacak."
        )
        await cls.send_message(token, chat_id, msg)
        return {"status": "ok", "active_agent": selected.name}

    @classmethod
    async def _handle_balance_command(cls, token: str, chat_id: str, user: User, db: AsyncSession) -> Dict[str, Any]:
        w_stmt = select(Wallet).where(Wallet.user_id == user.id)
        w_res = await db.execute(w_stmt)
        wallet = w_res.scalar_one_or_none()
        balance = f"${wallet.balance_usd:.4f} USD" if wallet else "$0.0000 USD"

        msg = (
            f"💳 *Cüzdan & Hesap Özeti*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Kullanıcı:* `{user.email}`\n"
            f"💰 *Kullanılabilir Bakiye:* `{balance}`\n"
            f"⚡ *Durum:* Aktif & Güvenli\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Bakiye yüklemek için web paneline gidebilirsiniz."
        )
        await cls.send_message(token, chat_id, msg)
        return {"status": "ok", "balance": balance}

    @classmethod
    async def _route_to_active_agent(cls, token: str, chat_id: str, text: str, user: User, db: AsyncSession) -> Dict[str, Any]:
        """Routes conversational requests to the user's active or best autonomous agent."""
        is_news = text.startswith("/news") or text.startswith("/haber") or text.startswith("/search")
        if is_news:
            parts = text.split(" ", 1)
            query_prompt = parts[1].strip() if len(parts) > 1 else "Gündem ve son dakika haberleri"
        else:
            query_prompt = text

        # Find active agent
        active_agent = None
        if user.telegram_active_agent_id:
            a_stmt = select(CustomAgent).where(CustomAgent.id == user.telegram_active_agent_id)
            a_res = await db.execute(a_stmt)
            active_agent = a_res.scalar_one_or_none()

        if not active_agent:
            a_stmt = select(CustomAgent).where(CustomAgent.user_id == user.id).order_by(CustomAgent.total_runs.desc())
            a_res = await db.execute(a_stmt)
            active_agent = a_res.scalar_one_or_none()

        if not active_agent:
            active_agent = CustomAgent(
                user_id=user.id,
                name="Canlı Haber & Web Asistanı",
                icon="📰",
                model_id="amazon.nova-micro-v1:0",
                system_prompt="Sen kullanıcının Telegram asistanısın. Canlı internet verilerini ve haberlerini analiz edip net, profesyonel ve emojilerle zenginleştirilmiş Türkçe özetler sunarsın.",
                tools_config={"web_search": True, "telegram": True}
            )

        await cls.send_message(token, chat_id, f"⚡ *{active_agent.icon} {active_agent.name} yanıt hazırlıyor...*")

        result = await AgentAutonomousEngine.run_agent(
            agent=active_agent,
            input_text=query_prompt,
            trigger_type="TELEGRAM_MESSAGE",
            db=db,
            telegram_chat_id=chat_id
        )

        output_text = result.get("output", "Yanıt üretilemedi.")
        header = f"{active_agent.icon} *{active_agent.name}:*\n\n"
        full_reply = f"{header}{output_text}"

        await cls.send_message(token, chat_id, full_reply)
        return {"status": "ok", "agent": active_agent.name}


    _polling_task: Optional[asyncio.Task] = None
    _is_polling: bool = False

    @classmethod
    async def start_polling_worker(cls):
        """Starts background self-healing Telegram long-polling worker."""
        if cls._is_polling:
            return
        token = get_telegram_bot_token()
        if not token:
            logger.warning("[TelegramBotService] No Telegram bot token configured. Polling worker disabled.")
            return
        cls._is_polling = True
        cls._polling_task = asyncio.create_task(cls._polling_loop())
        logger.info(f"[TelegramBotService] Background Telegram polling worker started for @{get_telegram_bot_username()}")

    @classmethod
    async def stop_polling_worker(cls):
        """Stops background Telegram polling worker cleanly."""
        cls._is_polling = False
        if cls._polling_task:
            cls._polling_task.cancel()
            try:
                await cls._polling_task
            except asyncio.CancelledError:
                pass
        logger.info("[TelegramBotService] Background Telegram polling worker stopped.")

    @classmethod
    async def _polling_loop(cls):
        from app.core.database import AsyncSessionLocal
        token = get_telegram_bot_token()
        if not token:
            return
        offset = 0
        url = f"{cls.TELEGRAM_API_BASE}{token}/getUpdates"
        logger.info(f"[TelegramBotService] Polling active for bot: @{get_telegram_bot_username()}")
        
        while cls._is_polling:
            try:
                async with httpx.AsyncClient(timeout=35.0) as client:
                    resp = await client.get(url, params={"offset": offset, "timeout": 20})
                    if resp.status_code == 200:
                        data = resp.json()
                        for update in data.get("result", []):
                            offset = update["update_id"] + 1
                            try:
                                async with AsyncSessionLocal() as db:
                                    await cls.process_webhook_update(token, update, db)
                            except Exception as update_err:
                                logger.error(f"[TelegramBotService] Error processing update: {update_err}")
                    elif resp.status_code == 409:
                        # Another instance active - backoff
                        logger.debug("[TelegramBotService] Another getUpdates instance active, backing off 5s...")
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[TelegramBotService] Polling exception (auto-recovering in 3s): {e}")
                await asyncio.sleep(3)


