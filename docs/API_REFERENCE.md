# 📡 REST API & Gateway Referansı (API Reference)

Bedrock AI Gateway ve Otonom Agent motorunun tüm REST API uç noktalarının teknik referans dokümanıdır. Tüm rotalar standart HTTP durum kodlarını, JWT Bearer yetkilendirmesini ve `x-api-key` başlığını destekler.

---

## ⚡ 1. Canlı Base URL & Yetkilendirme

* **Canlı Base URL:** `http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com`
* **Yetkilendirme Başlıkları:**
  - **Kullanıcı Girişi (JWT):** `Authorization: Bearer <jwt_access_token>`
  - **API Key Kullanımı:** `Authorization: Bearer bgk_<api_key>` veya `x-api-key: bgk_<api_key>`

---

## 💬 2. OpenAI Uyumlu Chat API (`/v1/chat/completions`)

OpenAI SDK, LangChain, LlamaIndex ve curl ile %100 uyumludur.

### İstek Formatı (POST `/v1/chat/completions`):
```bash
curl -X POST http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "anthropic.claude-3-7-sonnet-20250219-v1:0",
    "messages": [
      {"role": "system", "content": "Sen yardımcı bir asistansın."},
      {"role": "user", "content": "AWS Bedrock mimarisini 3 maddede özetle."}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

### Yanıt Formatı (JSON):
```json
{
  "id": "chatcmpl-bedrock-9b8f2a1c",
  "object": "chat.completion",
  "created": 1724851200,
  "model": "anthropic.claude-3-7-sonnet-20250219-v1:0",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "1. AWS Bedrock, sunucusuz yönetilen LLM servisidir...\n2. Converse API ile yerel araç çağrısı destekler...\n3. Entegre Guardrails ile veri güvenliği sağlar."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 42,
    "completion_tokens": 85,
    "total_tokens": 127
  }
}
```

---

## 🤖 3. Otonom Agent & Bilgi Tabanı API'leri

| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/api/agents` | Kullanıcının oluşturduğu tüm otonom botları listeler |
| `POST` | `/api/agents` | Yeni otonom bot oluşturur |
| `GET` | `/api/agents/{agent_id}` | Botun detaylarını, seviyesini ve araçlarını getirir |
| `PATCH` | `/api/agents/{agent_id}` | Bot ayarlarını, promptunu ve zamanlayıcısını günceller |
| `DELETE` | `/api/agents/{agent_id}` | Botu ve bağlı verilerini siler |
| `POST` | `/api/agents/{agent_id}/run` | Botu manuel olarak tetikler (ReAct döngüsünü çalıştırır) |
| `GET` | `/api/agents/{agent_id}/logs` | Botun geçmiş çalışma loglarını, tokenlarını ve süresini getirir |
| `POST` | `/api/agents/{agent_id}/knowledge` | Botun bilgi tabanına Website URL, API veya özel not ekler (RAG) |
| `DELETE` | `/api/agents/{agent_id}/knowledge/{source_id}` | Eklenmiş bilgi kaynağını siler |
| `POST` | `/api/agents/{agent_id}/feedback` | Botun yanıtına olumlu (+50 XP) veya olumsuz oy verir |
| `GET` | `/api/agents/{agent_id}/growth` | Botun XP puanını, Seviyesini (1-4), IQ skorunu ve gelişim geçmişini getirir |
| `POST` | `/api/agents/{agent_id}/reset-memory` | Botun öğrendiği uzun süreli semantik hafızayı sıfırlar |

---

## 📱 4. Telegram Bot Entegrasyon API'leri

| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/api/agents/telegram/status` | Telegram botunun bağlantı durumunu ve Chat ID'sini getirir |
| `POST` | `/api/agents/telegram/generate-code` | 6 haneli `TG-XXXXXX` eşleştirme kodu üretir |
| `POST` | `/api/agents/telegram/disconnect` | Telegram bot bağlantısını sonlandırır |
| `POST` | `/api/agents/telegram/test-message` | Bağlı Telegram hesabına test bildirimi gönderir |

---

## 🔑 5. API Keys & Cüzdan API'leri

| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/api/keys` | Aktif API anahtarlarını listeler |
| `POST` | `/api/keys` | Yeni API anahtarı üretir (`bgk_...`) |
| `DELETE` | `/api/keys/{key_id}` | API anahtarını iptal eder |
| `GET` | `/api/wallet` | Kullanıcının USD bakiye ve harcama detaylarını getirir |

---

## 📈 6. Sistem & İzleme API'leri

* `GET /health`: Sistem sağlık durumu (`{"status": "healthy", "service": "Bedrock AI Gateway"}`).
* `GET /metrics`: Prometheus metrik çıktısı (`gateway_requests_total`, `gateway_tokens_total`...).
