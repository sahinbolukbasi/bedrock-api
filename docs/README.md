# 📚 AWS Bedrock AI Gateway — Master Documentation & LLM Guide

Bu dizin, **AWS Bedrock AI Gateway Platformu** için tüm teknik mimariyi, AWS kaynak kataloğunu, API uç noktalarını, otonom ajan motorunu, izleme stack'ini ve yapay zeka geliştiricileri için el kitabını barındırır.

---

## 🧭 Dokümantasyon Modülleri

| Doküman | İçerik & Amaç |
| :--- | :--- |
| 🤖 **[AI_AGENT_PLAYBOOK.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/AI_AGENT_PLAYBOOK.md)** | **Yapay zeka ajanları & LLM'ler için sistemi bozmadan müdahale etme el kitabı** |
| 🌐 **[AWS_RESOURCE_CATALOG.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/AWS_RESOURCE_CATALOG.md)** | Resource Group (`bedrock-gateway-production-resources`), 36+ AWS kaynağının ARN ve ID haritası |
| 🏛️ **[ARCHITECTURE.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/ARCHITECTURE.md)** | ECS Fargate, ALB, RDS, ElastiCache, Secrets Manager ve Bedrock uçtan uca mimarisi |
| 📱 **[TELEGRAM_AND_AUTONOMOUS_BOTS.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/TELEGRAM_AND_AUTONOMOUS_BOTS.md)** | Telegram Botu (`@BedrocksAiBot`), Cron Scheduler, SNS SMS & SES Mail, Öğrenen Bellek Cache |
| 📡 **[API_REFERENCE.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/API_REFERENCE.md)** | OpenAI uyumlu `/v1/chat/completions`, `/v1/models` ve Gateway yönetim API uç noktaları |
| 🗄️ **[DATABASE_SCHEMA.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/DATABASE_SCHEMA.md)** | RDS PostgreSQL entity modelleri, ilişkiler, indeksler ve Redis anahtar yapısı |
| 📊 **[MONITORING_AND_LOGS.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/MONITORING_AND_LOGS.md)** | Grafana Dashboard, Prometheus metrikleri ve CloudWatch logları |
| 🚀 **[DEPLOYMENT.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/DEPLOYMENT.md)** | Terraform altyapı kurulumu, ECR build & push, ECS rolling deployment |
| 🔒 **[SECURITY.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/SECURITY.md)** | IAM least-privilege, API key hashleme, Redis token-bucket rate limiter, WAF |
| 🛠️ **[TROUBLESHOOTING.md](file:///Users/sahinbolukbasi/Development/bedrock/docs/TROUBLESHOOTING.md)** | 502 Bad Gateway, CloudWatch log akışları, Bedrock kota aşımı çözüm rehberi |

---

## ⚡ Canlı Sistem Bilgileri

* **Web Konsolu & Portalı:** `http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com`
* **API Ağ Geçidi:** `http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com:8000` (veya port 80 üzerinden `/api/*`, `/v1/*`)
* **Telegram Botu:** `@BedrocksAiBot` ([https://t.me/BedrocksAiBot](https://t.me/BedrocksAiBot))
* **AWS Bölgesi:** `us-east-1` (N. Virginia)
* **AWS Resource Group:** `bedrock-gateway-production-resources`
* **Admin Hesabı:** `admin@bedrockgateway.com` / `AdminPassword123!`
* **AWS Secrets Manager:** `bedrock-gateway-secrets-prod`
