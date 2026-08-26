# 🗄️ Veritabanı Şeması & Önbellek Mimarisi

Sistem, ilişkisel veri yönetimi için **Amazon RDS PostgreSQL 16**, token bucket rate-limiting ve oturum yönetimi için **Amazon ElastiCache Redis 7** kullanır.

---

## 📊 PostgreSQL Tablo Şeması (`backend/app/models/entities.py`)

### 1. `users` (Kullanıcılar)
* `id` (UUID, Primary Key)
* `email` (String, Unique, Index)
* `hashed_password` (String)
* `full_name` (String)
* `role` (String: `admin`, `developer`, `user`)
* `is_active` (Boolean)
* `is_verified` (Boolean)
* `mfa_enabled` (Boolean)
* `mfa_secret` (String, Optional)
* `created_at`, `updated_at` (DateTime)

### 2. `wallets` (Cüzdan & Bakiye)
* `id` (UUID, Primary Key)
* `user_id` (UUID, ForeignKey `users.id`, Unique)
* `balance_usd` (Numeric 12,6) — Kullanıcının kullanılabilir AI bakiye tutarı.
* `currency` (String, varsayılan `USD`)

### 3. `api_keys` (API Anahtarları)
* `id` (UUID, Primary Key)
* `user_id` (UUID, ForeignKey `users.id`, Index)
* `key_hash` (String, Unique, Index) — SHA256 ile hashlenmiş anahtar.
* `key_prefix` (String) — Arayüzde gösterim için ilk 8 karakter (`sk-live-...`).
* `name` (String)
* `rate_limit_rpm` (Integer)
* `is_active` (Boolean)

### 4. `model_catalogs` (AWS Bedrock Model Kataloğu)
* `id` (UUID, Primary Key)
* `model_id` (String, Unique, Index) — Örn: `amazon.nova-micro-v1:0`, `anthropic.claude-3-5-sonnet-20241022-v2:0`
* `display_name` (String)
* `provider` (String: `amazon`, `anthropic`, `meta`, `mistral`)
* `input_cost_per_1k` (Numeric 10,6)
* `output_cost_per_1k` (Numeric 10,6)
* `context_window` (Integer)
* `is_active` (Boolean)

### 5. `custom_agents` (Otonom Ajanlar & Botlar)
* `id` (UUID, Primary Key)
* `user_id` (UUID, ForeignKey `users.id`)
* `name` (String)
* `system_prompt` (Text)
* `model_id` (String)
* `schedule_cron` (String, Optional) — Cron takvimi (örn. `0 9 * * *`).
* `notify_telegram` (Boolean)
* `notify_sms` (Boolean)
* `notify_email` (Boolean)
* `phone_number` (String, Optional)
* `learned_memory_cache` (Text) — **Ajanın her görevde edindiği özet tecrübeleri tutan öğrenen bellek.**

### 6. `agent_execution_logs` (Ajan Çalışma Kayıtları)
* `id` (UUID, Primary Key)
* `agent_id` (UUID, ForeignKey `custom_agents.id`)
* `executed_at` (DateTime)
* `input_data` (Text)
* `output_response` (Text)
* `status` (String: `SUCCESS`, `FAILED`)
* `tokens_used` (Integer)
* `cost_usd` (Numeric 10,6)

---

## ⚡ Redis Önbellek Anahtar Yapısı

* `ratelimit:{key_id}:{timestamp_minute}`: Token bucket hız sınırlayıcı (RPM).
* `user_cache:{user_id}`: Kullanıcı kimlik ve rol bilgisi önbelleği (TTL: 300s).
* `agent_lock:{agent_id}`: Aynı ajanın eş zamanlı mükerrer çalışmasını engelleyen dağıtık kilit.
