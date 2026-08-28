# AWS Ürünleri ve Kaynak Kataloğu

Bedrock AI Gateway sistemi tarafından kullanılan AWS bulut servisleri ve modellerinin detaylı teknik kataloğudur.

---

## ☁️ 1. Kullanılan AWS Servisleri

| AWS Servisi | Kullanım Amacı | Konfigürasyon / Modül |
| :--- | :--- | :--- |
| **AWS Bedrock** | LLM, Akıl Yürütme ve Agent Motoru | Converse API with `toolConfig`, Streaming |
| **AWS Bedrock Guardrails** | PII Maskeleme & Prompt Injection Koruması | Content Policy & Sensitive Info Filter |
| **Amazon S3** | Bilgi Tabanı (Corpus) & Doküman Deposu | SSE-AES256 Şifreleme, Otomatik Chunking |
| **Amazon DynamoDB** | Stateful MCP Oturumu & Ajan Hafızası | Pay-Per-Request (On-Demand), TTL İndeksi |
| **AWS IAM & STS** | Least Privilege Rolleri & GitHub OIDC | Secretless CI/CD, AssumeRoleWithWebIdentity |

---

## 🧠 2. AWS Bedrock Model Kataloğu & Fiyatlandırma

### 2.1. Frontier & Akıl Yürütme Modelleri (Reasoning Tier)
- **Anthropic Claude 3.7 Sonnet (Hybrid Reasoning):**
  - Model ID: `anthropic.claude-3-7-sonnet-20250219-v1:0`
  - Bağlam Penceresi: 200,000 Token
  - Kullanım: Karmaşık kod üretimi, mimari analiz, çok adımlı ReAct araştırmaları.
  - Maliyet: $0.003 / 1k girdi — $0.015 / 1k çıktı.

- **Anthropic Claude 3.5 Sonnet v2:**
  - Model ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
  - Bağlam Penceresi: 200,000 Token
  - Kullanım: Yüksek kaliteli sohbet ve görsel (vision) analizi.
  - Maliyet: $0.003 / 1k girdi — $0.015 / 1k çıktı.

### 2.2. Hızlı & Düşük Maliyetli Agent Modelleri (Economy Tier)
- **Anthropic Claude 3.5 Haiku:**
  - Model ID: `anthropic.claude-3-5-haiku-20241022-v1:0`
  - Bağlam Penceresi: 200,000 Token
  - Kullanım: Hızlı veri formatlama, özetleme ve anlık bot yanıtları.
  - Maliyet: $0.0008 / 1k girdi — $0.004 / 1k çıktı.

- **Amazon Nova Micro:**
  - Model ID: `amazon.nova-micro-v1:0`
  - Bağlam Penceresi: 128,000 Token
  - Kullanım: Ultra düşük maliyetli otonom cron görevleri ve sınıflandırma.
  - Maliyet: **$0.000035 / 1k girdi — $0.00014 / 1k çıktı**.

- **Amazon Nova Lite & Nova Pro:**
  - Model ID: `amazon.nova-lite-v1:0` / `amazon.nova-pro-v1:0`
  - Multimodal metin ve görsel işleme kabiliyeti.

### 2.3. Embedding & Görsel Üretim
- **Amazon Titan Text Embeddings v2:**
  - Model ID: `amazon.titan-embed-text-v2:0`
  - Vektör Boyutları: 1536, 512, 256
  - Kullanım: Doküman vektörleştirme ve anlamsal arama.

- **Amazon Titan Image Generator G1:**
  - Model ID: `amazon.titan-image-generator-v1`
  - Kullanım: 1024x1024 görsel ve grafik üretimi.

---

## 💰 3. Maliyet Optimizasyonu Stratejileri

1. **Dinamik Model Yönlendirme:** Basit işlemler Amazon Nova Micro veya Claude 3.5 Haiku'ya; karmaşık muhakeme Claude 3.7 Sonnet'e yönlendirilir (**%70+ tasarruf**).
2. **3-Katmanlı Hafıza Sıkıştırması:** Eski mesajlar tek paragrafa özetlenir (**%75+ token tasarrufu**).
3. **Maliyetsiz Yerel RAG:** Harici veritabanı maliyeti oluşturmadan süreç içi BM25/Cosine indeksleme kullanılır.
