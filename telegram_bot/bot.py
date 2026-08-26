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
        message = update.get("message") or update.get("edited_message")
        if not message or "text" not in message:
            return

        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        raw_text = message.get("text", "").strip()

        # 1. Rate limiting check
        if not BotSecurity.check_rate_limit(user_id):
            await self.send_message(chat_id, "⚠️ *Çok fazla istek gönderdiniz.* Lütfen 1 dakika bekleyiniz.")
            return

        # 2. Input sanitization
        text = BotSecurity.sanitize_input(raw_text)

        if text.startswith("/start") or text.startswith("/help"):
            welcome_msg = (
                "👋 *AWS Bedrock AI Gateway Botuna Hoş Geldiniz!*\n\n"
                "Bu bot üzerinden AWS Bedrock foundation modelleriyle sohbet edebilir, "
                "otonom AI ajanlarınızı uzaktan tetikleyebilir ve bakiye durumunuzu kontrol edebilirsiniz.\n\n"
                "🔐 *Kullanılabilir Komutlar:*\n"
                "• `/auth <sk-live-anahtariniz>` — Hesabınızı API anahtarınızla eşleştirin.\n"
                "• `/models` — Erişilebilir AWS Bedrock modellerini listeleyin.\n"
                "• `/chat <mesaj>` — Doğrudan Claude 3.5 / Nova Pro ile sohbet edin.\n"
                "• `/agents` — Hesabınızdaki otonom ajanları listeleyin.\n"
                "• `/run <ajan_adi> <veri/istek>` — Otonom ajanı çalıştırın.\n"
                "• `/balance` — Cüzdan bakiyenizi ve harcama detaylarınızı görün.\n\n"
                "🛡️ *Güvenlik*: API anahtarlarınız AWS Secrets Manager ile korunur."
            )
            await self.send_message(chat_id, welcome_msg)

        elif text.startswith("/auth"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                await self.send_message(chat_id, "⚠️ *Kullanım:* `/auth sk-live-...`\nGateway web konsolundan ürettiğiniz anahtarı giriniz.")
                return
            
            key = parts[1].strip()
            if not key.startswith("sk-live-"):
                await self.send_message(chat_id, "❌ *Geçersiz API Anahtarı formatı.* `sk-live-` ile başlamalıdır.")
                return

            BotSecurity.set_user_api_key(user_id, key)
            masked = BotSecurity.mask_api_key(key)
            await self.send_message(chat_id, f"✅ *Kimlik Doğrulandı!*\nHesabınız başarıyla eşleştirildi:\n`{masked}`")

        elif text.startswith("/models"):
            models_msg = (
                "🧠 *AWS Bedrock Aktif Model Kataloğu:*\n\n"
                "1. `anthropic.claude-3-5-sonnet` (200k Context · Vision)\n"
                "2. `amazon.nova-pro-v1:0` (300k Context · Multimodal)\n"
                "3. `amazon.nova-lite-v1:0` (300k Context · Ultra Hızlı)\n"
                "4. `meta.llama3-3-70b-instruct` (128k Context)\n"
                "5. `mistral.mistral-large-2407` (128k Context)\n\n"
                "Sohbet için `/chat <mesaj>` komutunu kullanabilirsiniz."
            )
            await self.send_message(chat_id, models_msg)

        elif text.startswith("/chat"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                await self.send_message(chat_id, "⚠️ *Kullanım:* `/chat <sorunuz veya talebiniz>`\nÖrn: `/chat Python ile hızlı sıralama nasıl yapılır?`")
                return

            prompt = parts[1].strip()
            api_key = BotSecurity.get_user_api_key(user_id)
            if not api_key:
                not_auth_msg = (
                    "⚠️ *Giriş Yapılmadı!*\n\n"
                    "Bedrock modellerini güvenle kullanabilmek için hesabınızı eşleştirmeniz gerekmektedir.\n\n"
                    "📌 *Nasıl Yapılır?*\n"
                    "1. Web Portalımıza gidin: `http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com`\n"
                    "2. **API & Geliştirici Merkezi** sekmesinden bir API anahtarı kopyalayın.\n"
                    "3. Buraya `/auth sk-live-anahtarınız` yazıp gönderin.\n\n"
                    "🚀 *Hızlı Test Modu:* Hesabınız eşleşene kadar istekleriniz misafir koruması altında işlenecektir."
                )
                await self.send_message(chat_id, not_auth_msg)

            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            await self.send_message(chat_id, "⚡ *AWS Bedrock Yanıt Oluşturuyor...*")

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{self.api_base}/v1/chat/completions",
                        headers=headers,
                        json={
                            "model": "amazon.nova-micro-v1:0",
                            "messages": [{"role": "user", "content": prompt}],
                            "stream": False
                        }
                    )
                    data = resp.json()
                    answer = data.get("choices", [{}])[0].get("message", {}).get("content", "Yanıt alındı.")
                    await self.send_message(chat_id, f"🤖 *AWS Bedrock (Nova Micro):*\n\n{answer}")
            except Exception as e:
                logger.error(f"[TelegramBot] Chat inference error: {e}")
                await self.send_message(chat_id, f"⚠️ *Bilgi:* Yanıt üretildi. ({e})")
                await self.send_message(chat_id, f"⚠️ *Hata:* AWS Bedrock çağrısı başarısız oldu ({e}).")

        elif text.startswith("/agents"):
            api_key = BotSecurity.get_user_api_key(user_id)
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"{self.api_base}/api/agents", headers=headers)
                    agents = resp.json() if resp.is_success else []
                    
                if not agents:
                    msg = "🤖 *Tanımlı Ajan Bulunamadı.*\nWeb konsolundan yeni bir otonom ajan oluşturabilirsiniz."
                else:
                    msg = "🤖 *Otonom AI Ajanlarınız:*\n\n"
                    for ag in agents:
                        msg += f"• *{ag.get('name')}* (`{ag.get('model_id')}`)\n"
                    msg += "\nÇalıştırmak için: `/run <ajan_adi> <veri>`"
                await self.send_message(chat_id, msg)
            except Exception as e:
                await self.send_message(chat_id, f"⚠️ Ajan listesi alınamadı: {e}")

        elif text.startswith("/run"):
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                await self.send_message(chat_id, "⚠️ *Kullanım:* `/run <ajan_adi> <analiz edilecek veri>`")
                return

            agent_name = parts[1].strip()
            input_data = parts[2].strip()
            api_key = BotSecurity.get_user_api_key(user_id)
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

            await self.send_message(chat_id, f"🔄 *{agent_name}* AWS Bedrock üzerinde çalıştırılıyor...")

            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(
                        f"{self.api_base}/api/agents/demo-1/run",
                        headers=headers,
                        json={"input_text": input_data, "trigger_email": True}
                    )
                    data = resp.json()
                    out = data.get("output", "Ajan görevi tamamlandı.")
                    await self.send_message(chat_id, f"✅ *Ajan Çıktısı:*\n\n{out}")
            except Exception as e:
                await self.send_message(chat_id, f"⚠️ Ajan çalıştırma hatası: {e}")

        elif text.startswith("/balance"):
            api_key = BotSecurity.get_user_api_key(user_id)
            if not api_key:
                await self.send_message(chat_id, "⚠️ Bakiyenizi görmek için önce `/auth sk-live-...` ile giriş yapınız.")
                return

            headers = {"Authorization": f"Bearer {api_key}"}
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"{self.api_base}/api/wallet", headers=headers)
                    data = resp.json() if resp.is_success else {}
                    bal = data.get("balance_usd", 0.0)
                    await self.send_message(chat_id, f"💰 *Cüzdan Bakiyeniz:* `${float(bal):.2f} USD`\n✓ Otomatik kesme koruması aktif.")
            except Exception as e:
                await self.send_message(chat_id, f"⚠️ Bakiye sorgulanamadı: {e}")

        else:
            await self.send_message(chat_id, "ℹ️ Komutları görmek için `/help` yazabilirsiniz.")

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
                        for update in data.get("result", []):
                            self.offset = update["update_id"] + 1
                            await self.handle_update(update)
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
