import asyncio
import httpx
import sys
from loguru import logger
from .config import config
from .security import BotSecurity

# Configure structured logging
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

class BedrockTelegramBot:
    """
    Production Telegram Bot for Bedrock AI Gateway.
    Runs via long-polling or webhook to manage models, trigger agents, and run live inference.
    """

    def __init__(self):
        config.load_from_aws_secrets()
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.api_base = config.API_BASE_URL
        self.base_tg_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.offset = 0

    async def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Safely dispatches markdown messages to Telegram with character chunking.
        """
        url = f"{self.base_tg_url}/sendMessage"
        # Telegram max message length is 4096
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            for chunk in chunks:
                try:
                    payload = {
                        "chat_id": chat_id,
                        "text": chunk,
                        "parse_mode": parse_mode
                    }
                    resp = await client.post(url, json=payload)
                    if not resp.is_success:
                        # Fallback without parse_mode if markdown is invalid
                        payload.pop("parse_mode")
                        await client.post(url, json=payload)
                except Exception as e:
                    logger.error(f"[TelegramBot] Failed to send message to {chat_id}: {e}")
                    return False
        return True

    async def handle_update(self, update: dict):
        message = update.get("message") or update.get("edited_message") or update.get("callback_query")
        if not message:
            return

        user_info = message.get("from", {})
        user_id = user_info.get("id")
        if user_id and not BotSecurity.check_rate_limit(user_id):
            chat_id = message.get("chat", {}).get("id") or message.get("message", {}).get("chat", {}).get("id")
            if chat_id:
                await self.send_message(chat_id, "⚠️ *Çok fazla istek gönderdiniz.* Lütfen biraz bekleyiniz.")
            return

        # Forward update to backend hybrid engine
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.api_base}/api/agents/telegram/webhook?bot_token={self.bot_token}",
                    json=update
                )
                if resp.is_success:
                    return
        except Exception as e:
            logger.warning(f"[TelegramBot] Forward to backend webhook failed: {e}. Executing fallback...")

        # Fallback local handler if backend is temporarily unreachable
        chat_id = message.get("chat", {}).get("id")
        raw_text = message.get("text", "").strip()
        if chat_id and raw_text.startswith("/start"):
            await self.send_message(
                chat_id,
                "👋 *AWS Bedrock AI Gateway Botu Aktif!*\n\n"
                "Hesabınızı bağlamak için web panelinden aldığınız kodu giriniz:\n"
                "`/pair TG-XXXXXX`\n\n"
                "⚡ Komutlar: `/remind`, `/track`, `/image`, `/agents`, `/haber`"
            )

    async def start_polling(self):
        """
        Long-polling loop for receiving Telegram updates in real-time.
        """
        logger.info(f"[TelegramBot] Starting polling with Bot Token: {BotSecurity.mask_api_key(self.bot_token)}")
        url = f"{self.base_tg_url}/getUpdates"

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                try:
                    resp = await client.get(url, params={"offset": self.offset, "timeout": 20})
                    if resp.is_success:
                        data = resp.json()
                        for update_item in data.get("result", []):
                            self.offset = update_item["update_id"] + 1
                            await self.handle_update(update_item)
                    await asyncio.sleep(0.5)
                except asyncio.CancelledError:
                    logger.info("[TelegramBot] Polling stopped.")
                    break
                except Exception as e:
                    logger.error(f"[TelegramBot] Polling error: {e}")
                    await asyncio.sleep(3)


if __name__ == "__main__":
    bot = BedrockTelegramBot()
    asyncio.run(bot.start_polling())

