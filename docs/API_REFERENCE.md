# 📡 API Referansı & Uç Noktalar

Gateway, standart **OpenAI Chat Completions** formatıyla %100 uyumludur ve platform yönetim servisleri sunar.

---

## 🤖 1. OpenAI Uyumlu API (`/v1`)

### `POST /v1/chat/completions`
* **Açıklama:** AWS Bedrock modelleriyle (Nova, Claude, Llama vb.) sohbet tamamlama veya SSE stream akışı üretir.
* **Başlıklar:**
  * `Authorization: Bearer sk-live-...`
  * `Content-Type: application/json`
* **İstek Gövdesi Örneği:**
```json
{
  "model": "amazon.nova-micro-v1:0",
  "messages": [
    { "role": "system", "content": "Kısa ve öz Türkçe yanıt ver." },
    { "role": "user", "content": "AWS Bedrock nedir?" }
  ],
  "stream": false
}
```

### `GET /v1/models`
* **Açıklama:** Erişilebilir ve aktif olan tüm AWS Bedrock modellerini döndürür.

---

## 🛠️ 2. Platform & Yönetim API (`/api`)

* `POST /api/auth/register` — Yeni kullanıcı kaydı ve cüzdan oluşturma.
* `POST /api/auth/login` — JWT erişim anahtarı ve rol döndürür.
* `GET /api/wallet` — Kullanıcının kalan bakiye miktarını sorgular.
* `GET /api/keys` — Kullanıcının aktif API anahtarlarını listeler.
* `POST /api/keys` — Yeni `sk-live-...` API anahtarı üretir.
* `GET /api/agents` — Otonom ajanları listeler.
* `POST /api/agents` — Yeni otonom ajan tanımlar.
* `POST /api/agents/{agent_id}/run` — Ajanı anında tetikler ve SMS/Telegram/E-posta ile sonucu iletir.
* `POST /api/agents/{agent_id}/reset-memory` — Ajanın öğrenen bellek önbelleğini sıfırlar.
