# 🤖 AI Agent & LLM Geliştirici El Kitabı (Playbook)

> **Kritik Kural:** Bu sistem canlıda (production) çalışan, gerçek AWS Bedrock foundation modelleriyle, RDS PostgreSQL ve ElastiCache ile entegre bir yapay zeka ağ geçididir. Yapılan her değişiklikte bu el kitabındaki prensiplere kesinlikle uyulmalıdır.

---

## 🛑 Altın Kurallar (Asla İhlal Edilemez)

1. **Statik Mock Veri Eklemeyin:** Sistem her zaman AWS Bedrock Runtime (`boto3.client('bedrock-runtime')`), AWS Secrets Manager, RDS PostgreSQL ve ElastiCache ile canlı çalışır. Asla `mock_response` gibi sahte string dizileri döndürmeyin.
2. **Localhost Kullanmayın:** Canlı ortamda tüm bağlantılar AWS ALB (`http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com`), RDS ve ElastiCache endpointleri üzerinden yapılır.
3. **Secrets Manager Senkronizasyonu:** Gizli değişkenler (`TELEGRAM_BOT_TOKEN`, `SECRET_KEY`, `DATABASE_URL` vb.) AWS Secrets Manager (`bedrock-gateway-secrets-prod`) üzerinden yüklenir. Kod içine asla gizli anahtar yazmayın.
4. **Mevcut Özellikleri Korumak:** Sohbet geçmişi, ses sentezi, otonom ajan motoru, SMS/Telegram bildirimleri, Stripe cüzdan kontrolü gibi kurulu bileşenlerin çalışan API sözleşmelerini bozmayın.

---

## 🛠️ Hata Çözme & Müdahale Akışı

### Senaryo 1: Backend "502 Bad Gateway" veya "Failed to fetch" Veriyor
1. **ECS Görev Durumunu İnceleyin:**
   ```bash
   aws ecs list-tasks --region us-east-1 --cluster bedrock-gateway-cluster --service-name bedrock-gateway-backend-svc
   ```
2. **CloudWatch Loglarını Kontrol Edin:**
   ```bash
   aws logs describe-log-streams --region us-east-1 --log-group-name /ecs/bedrock-gateway --order-by LastEventTime --descending --limit 1
   # Akış adını alıp logları okuyun:
   aws logs get-log-events --region us-east-1 --log-group-name /ecs/bedrock-gateway --log-stream-name "<STREAM_NAME>"
   ```
3. **Import veya Başlatma Hatasını Çözün:**
   * Python import hataları (`NameError`, `ImportError`, eksik tip tanımları) `uvicorn` sunucusunun çökmesine neden olur.
   * `backend/app/main.py`, `backend/app/providers/bedrock.py` ve `backend/app/api/*.py` dosyalarını kontrol edin.

---

### Senaryo 2: Telegram Botu Cevap Vermiyor
1. **Daemon Sürecini Kontrol Edin:**
   * Bot `telegram_bot/bot.py` üzerinden bağımsız async long-polling olarak çalışır.
2. **Secrets Manager Token Kontrolü:**
   ```bash
   aws secretsmanager get-secret-value --region us-east-1 --secret-id bedrock-gateway-secrets-prod --query SecretString --output text
   ```
3. **Lokal veya Cloud Daemon'ı Başlatma:**
   ```bash
   ./venv/bin/python -m telegram_bot.bot
   ```

---

### Senaryo 3: Yeni Bir Bedrock Modeli Eklemek
1. `backend/app/core/seed.py` dosyasına model kimliğini ve fiyatlandırmasını (Input/Output token maliyeti) ekleyin.
2. `backend/app/providers/bedrock.py` içindeki desteklenen model eşlemelerine ekleyin.
3. Bedrock Converse API standardına uygun mesaj formatı kullanıldığından emin olun.
