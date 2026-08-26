# 📚 AWS Bedrock AI Gateway — Ana Dokümantasyon & LLM Yönergesi

Bu dizin, **AWS Bedrock AI Gateway** platformunun tüm mimarisini, AWS servis haritasını, veritabanı şemasını, API uç noktalarını, otonom ajan motorunu, izleme katmanını ve yapay zeka ajanlarının (LLM pair-programmers) sistemi bozmadan müdahale edebilmeleri için gereken kuralları içerir.

---

## 🧭 Dokümantasyon İndeksi

| Doküman | Açıklama |
| :--- | :--- |
| [ARCHITECTURE.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/ARCHITECTURE.md) | Uçtan uca AWS altyapı ve sistem mimarisi |
| [AWS_RESOURCE_CATALOG.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/AWS_RESOURCE_CATALOG.md) | AWS Resource Group, tüm 36+ AWS kaynağının ARN ve ID listesi |
| [AI_AGENT_PLAYBOOK.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/AI_AGENT_PLAYBOOK.md) | LLM'lerin kod yazma, hata ayıklama ve güvenli geliştirme kuralları |
| [DATABASE_SCHEMA.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/DATABASE_SCHEMA.md) | RDS PostgreSQL modelleri, tablolar, Redis önbellek yapısı |
| [TELEGRAM_AND_AUTONOMOUS_BOTS.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/TELEGRAM_AND_AUTONOMOUS_BOTS.md) | Telegram Botu (`@BedrocksAiBot`), Cron Scheduler, SNS SMS & SES Mail |
| [API_REFERENCE.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/API_REFERENCE.md) | OpenAI uyumlu `/v1` ve Gateway platform API uç noktaları |
| [MONITORING_AND_LOGS.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/MONITORING_AND_LOGS.md) | Grafana Dashboard, Prometheus metrikleri ve CloudWatch logları |

---

## ⚡ Hızlı Özet & Canlı Bilgiler

* **Web Portalı (Frontend):** `http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com`
* **API Ağ Geçidi (Backend):** `http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com:8000` (veya port 80 path routing `/api/*`, `/v1/*`)
* **Telegram Botu:** `@BedrocksAiBot` (`https://t.me/BedrocksAiBot`)
* **AWS Bölgesi:** `us-east-1` (N. Virginia)
* **AWS Resource Group:** `bedrock-gateway-production-resources`
* **Süper Yönetici Girişi:** `admin@bedrockgateway.com` / `AdminPassword123!`
* **AWS Secrets Manager:** `bedrock-gateway-secrets-prod`
