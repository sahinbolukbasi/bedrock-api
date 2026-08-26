# 🤖 AWS Bedrock Gateway — Telegram Bot Servisi

AWS Bedrock Frontier AI modellerine Telegram üzerinden güvenli ve şifrelenmiş erişim sağlayan otonom bot servisi.

## 🔐 Güvenlik Mimarisi
1. **AWS Secrets Manager**: Bot tokenı ve API gizli anahtarları statik kod yerine doğrudan `bedrock-gateway-secrets-prod` kasasından çekilir.
2. **Kullanıcı Doğrulama & İzolasyon**: `/auth <sk-live-...>` komutu ile Telegram kullanıcıları Gateway hesapları ile güvenle eşleşir.
3. **Hız Sınırlama (Rate Limiting)**: Dakika başına 30 istek tavan limitiyle DDoS ve maliyet patlamalarına karşı korunur.
4. **Girdi Arındırma**: Prompt injection ve zararlı kontrol karakterleri regex filtrelerinden geçirilir.

## 🚀 Kullanıcı Komutları

| Komut | Açıklama |
| :--- | :--- |
| `/start` / `/help` | Hoş geldiniz mesajı ve komut rehberi |
| `/auth <api_key>` | Telegram hesabınızı Gateway API anahtarınız ile eşleştirir |
| `/models` | Erişilebilir AWS Bedrock modellerini (Claude 3.5, Nova Pro vb.) listeler |
| `/chat <mesaj>` | AWS Bedrock foundation modelleri ile doğrudan sohbet eder |
| `/agents` | Hesabınızdaki otonom AI ajanlarını listeler |
| `/run <ajan> <veri>` | Belirtilen ajanı çalıştırıp çıktısını Telegram'a döner |
| `/balance` | Canlı cüzdan bakiyenizi ve harcama detaylarınızı görüntüler |

## 📦 Kurulum ve Çalıştırma

```bash
# Bağımlılıkları yükleyin
pip install -r telegram_bot/requirements.txt

# Botu başlatın
python -m telegram_bot.bot
```
