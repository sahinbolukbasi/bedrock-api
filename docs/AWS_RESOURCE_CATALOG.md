# 🌐 AWS Kaynak Kataloğu & Altyapı Envanteri (AWS Resource Catalog)

Bu doküman; AWS Bedrock AI Gateway platformunun canlı üretim ortamında kullandığı **tüm AWS kaynaklarının tam ARN'lerini, ID'lerini, modellerini ve fiyatlandırmasını** listeler.

---

## 🏛️ 1. Genel AWS Altyapı ve Ağ Kaynakları

* **AWS Bölgesi:** `us-east-1` (US East - N. Virginia)
* **AWS Resource Group:** `bedrock-gateway-production-resources`
* **AWS Application Load Balancer (ALB):**
  - **DNS Adresi:** `bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com`
  - **Portlar:** 80 (HTTP / Web), 443 (HTTPS), 8000 (Backend API), 3001 (Grafana İzleme)

---

## 📦 2. AWS ECS Fargate Konteyner Servisleri

| Servis Adı | Port | Konteyner İmajı (ECR) | Rol / Görev |
| :--- | :---: | :--- | :--- |
| **`bedrock-gateway-backend-svc`** | `8000` | `bedrock-gateway-backend:latest` | FastAPI Asenkron API, ReAct Motoru, Yerel RAG |
| **`bedrock-gateway-frontend-svc`** | `3000` | `bedrock-gateway-frontend:latest` | Next.js 14 Web Portalı, 4-Step Bot Sihirbazı |
| **`bedrock-gateway-telegram-svc`** | - | `bedrock-gateway-telegram-bot:latest` | Çift Yönlü Telegram Asistan Botu Worker'ı |
| **`bedrock-gateway-monitoring-svc`**| `3000/9090` | `bedrock-gateway-monitoring:latest` | Grafana 10.4 Dashboard & Prometheus Metrik Motoru |

---

## 🗄️ 3. AWS Veri, Önbellek & Güvenlik Servisleri

### 3.1. AWS RDS PostgreSQL (Multi-AZ)
- **Endpoint:** `bedrock-gateway-db.cobqqmqcs7xh.us-east-1.rds.amazonaws.com:5432`
- **Veritabanı Adı:** `bedrock_gateway`
- **Motor:** PostgreSQL 16 (Multi-AZ High Availability)
- **Kullanım:** Kullanıcı hesapları, API anahtarları, Özel bot tanımları, Büyüme & XP kayıtları, Çalışma logları.

### 3.2. AWS ElastiCache Redis Cluster
- **Endpoint:** `bedrock-gateway-redis.hmoplf.0001.use1.cache.amazonaws.com:6379`
- **Kullanım:** JWT oturum doğrulama, Token-Bucket Rate Limiter, Dağıtık işlem kilitleri (Distributed Locks).

### 3.3. AWS Secrets Manager
- **Secret ID:** `bedrock-gateway-secrets-prod`
- **Secret ARN:** `arn:aws:secretsmanager:us-east-1:996270854731:secret:bedrock-gateway-secrets-prod-8ZOYeZ`
- **İçerdiği Anahtarlar:** `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `TELEGRAM_BOT_TOKEN`, `STRIPE_SECRET_KEY`.

### 3.4. Amazon S3 Artifacts Bucket
- **Bucket Adı:** `bedrock-gateway-artifacts-prod`
- **Şifreleme:** SSE-AES256 Server-Side Encryption
- **Kullanım:** Kullanıcı dokümanları, RAG indeks dosyaları, bot tarafından üretilen indirilebilir grafik ve görseller.

### 3.5. Amazon CloudWatch
- **Log Grubu:** `/ecs/bedrock-gateway`
- **Metrik Ad Alanı:** `AWS/ECS`, `AWS/RDS`, `AWS/Bedrock`

---

## 🧠 4. AWS Bedrock Model Kataloğu & Fiyatlandırma

### 4.1. Akıl Yürütme & Frontier Modelleri (Reasoning Tier)
- **Anthropic Claude 3.7 Sonnet (Hybrid Reasoning):**
  - Model ID: `anthropic.claude-3-7-sonnet-20250219-v1:0`
  - Bağlam: 200k Token | Kullanım: Karmaşık analiz, mimari kod üretimi | Girdi: $0.003/1k - Çıktı: $0.015/1k.
- **Anthropic Claude 3.5 Sonnet v2:**
  - Model ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
  - Bağlam: 200k Token | Kullanım: Yüksek kaliteli sohbet ve görsel (vision) analizi | Girdi: $0.003/1k - Çıktı: $0.015/1k.

### 4.2. Hızlı & Düşük Maliyetli Agent Modelleri (Economy Tier)
- **Anthropic Claude 3.5 Haiku:**
  - Model ID: `anthropic.claude-3-5-haiku-20241022-v1:0`
  - Bağlam: 200k Token | Kullanım: Hızlı soru-cevap, canlı asistanlık | Girdi: $0.0008/1k - Çıktı: $0.004/1k.
- **Amazon Nova Micro:**
  - Model ID: `amazon.nova-micro-v1:0`
  - Bağlam: 128k Token | Kullanım: Ultra düşük maliyetli otonom cron görevleri | Girdi: **$0.000035/1k** - Çıktı: **$0.00014/1k**.
- **Amazon Nova Lite & Nova Pro:**
  - Model ID: `amazon.nova-lite-v1:0` / `amazon.nova-pro-v1:0`
  - Multimodal metin ve görsel işleme kabiliyeti.

### 4.3. Embedding & Görsel Üretim Modelleri
- **Amazon Titan Text Embeddings v2:**
  - Model ID: `amazon.titan-embed-text-v2:0`
  - Boyutlar: 1536 / 512 / 256 | Kullanım: Doküman vektörleştirme.
- **Amazon Titan Image Generator G1:**
  - Model ID: `amazon.titan-image-generator-v1`
  - Kullanım: 1024x1024 görsel ve grafik üretimi.
