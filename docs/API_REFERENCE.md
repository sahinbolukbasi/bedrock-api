# REST API Referansı (API Reference)

Bedrock AI Gateway ve Otonom Agent sisteminin tüm REST API uç noktaları.

---

## 🤖 1. Otonom Agent & Bilgi Tabanı API'leri

| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/api/agents` | Kullanıcının tüm otonom botlarını listeler |
| `POST` | `/api/agents` | Yeni otonom bot oluşturur |
| `PATCH` | `/api/agents/{agent_id}` | Bot ayarlarını ve promptunu günceller |
| `DELETE` | `/api/agents/{agent_id}` | Botu siler |
| `POST` | `/api/agents/{agent_id}/run` | Botu interaktif veya zamanlı tetikler |
| `GET` | `/api/agents/{agent_id}/logs` | Botun geçmiş çalışma loglarını ve maliyetini getirir |
| `POST` | `/api/agents/{agent_id}/knowledge` | Botun bilgi tabanına Website URL, API veya doküman ekler (RAG) |
| `DELETE` | `/api/agents/{agent_id}/knowledge/{source_id}` | Eklenmiş bilgi kaynağını siler |
| `POST` | `/api/agents/{agent_id}/feedback` | Botun yanıtına olumlu/olumsuz geri bildirim verir (+50 XP) |
| `GET` | `/api/agents/{agent_id}/growth` | Botun XP, Seviye (1-4), IQ skoru ve evrim geçmişini getirir |
| `POST` | `/api/agents/{agent_id}/reset-memory` | Botun öğrenilen uzun süreli hafızasını sıfırlar |

---

## 📱 2. Telegram Bot Entegrasyon API'leri

| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/api/agents/telegram/status` | Telegram botunun bağlantı durumunu getirir |
| `POST` | `/api/agents/telegram/generate-code` | Eşleştirme için 6 haneli `TG-XXXXXX` kodu üretir |
| `POST` | `/api/agents/telegram/disconnect` | Telegram bot bağlantısını sonlandırır |
| `POST` | `/api/agents/telegram/test-message` | Bağlı Telegram hesabına test bildirimi gönderir |

---

## 💬 3. OpenAI Uyumlu Chat API (`/v1/chat/completions`)

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "anthropic.claude-3-7-sonnet-20250219-v1:0",
    "messages": [
      {"role": "system", "content": "Sen yardımcı bir asistansın."},
      {"role": "user", "content": "Bugünkü yapay zeka haberlerini özetle."}
    ],
    "temperature": 0.7
  }'
```
