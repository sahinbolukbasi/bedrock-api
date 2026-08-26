# 🤖 Telegram Botu & Otonom Ajan Çalıştırma Platformu

Bu modül, kullanıcıların ve geliştiricilerin kendi yapay zeka ajanlarını oluşturup, arka planda zamanlanmış (cron) görevlerle veri takibi yaptırmasını ve elde edilen sonuçları **Telegram**, **SMS (AWS SNS)** ve **E-Posta (AWS SES)** ile iletmesini sağlar.

---

## 📱 Telegram Botu Kimliği & Kurulum

* **Bot Handle:** `@BedrocksAiBot` ([https://t.me/BedrocksAiBot](https://t.me/BedrocksAiBot))
* **Kaynak Kod Dizini:** `telegram_bot/`
* **Daemon Çalıştırma:** `./venv/bin/python -m telegram_bot.bot`
* **Gizli Anahtar:** AWS Secrets Manager (`bedrock-gateway-secrets-prod`) altındaki `TELEGRAM_BOT_TOKEN`.

### 🔑 Kullanıcı Kimlik Doğrulama (Onboarding Akışı)
1. Kullanıcı bot ile ilk kez konuştuğunda `/start` veya herhangi bir mesaj attığında rehber mesajı alır.
2. Web konsolundan `sk-live-...` API anahtarını kopyalar.
3. Bota `/auth sk-live-...` komutunu gönderir.
4. Bot, API anahtarını güvenli şekilde maskeleyerek kullanıcı Telegram ID'si ile eşleştirir.

---

## ⏱️ Otonom Ajan Motoru (`backend/app/services/scheduler.py`)

### 1. Zamanlayıcı (Cron Scheduler)
Ajanlar periyodik olarak çalışabilir:
* **Saatlik:** `0 * * * *`
* **Günlük:** `0 9 * * *` (Her gün sabah 09:00)
* **Haftalık:** `0 9 * * 1` (Pazartesi sabah 09:00)

### 2. Kendi Kendini Eğiten Bellek (Self-Improving Reflection Cache)
* Ajan her çalıştığında ürettiği analizin özetini `learned_memory_cache` sütununa kaydeder.
* Bir sonraki çalıştırmada bu bellek ajanın sistem talimatına (system prompt) otomatik olarak enjekte edilir.
* **Sonuç:** Sıfır fine-tuning maliyetiyle ajan her görevde daha tecrübeli ve isabetli hale gelir.

### 3. Çoklu Kanal Bildirim Dağıtımı
* **Telegram:** `TelegramBotService.send_alert(chat_id, message)`
* **SMS (AWS SNS):** `sns.publish(PhoneNumber=phone_number, Message=summary)`
* **E-Posta (AWS SES):** `EmailService.send_agent_report_email(to_email, report_html)`
