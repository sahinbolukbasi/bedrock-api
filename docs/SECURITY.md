# 🔒 Güvenlik, DevSecOps & Metrik Koruma Standartları (Security Specification)

Bu doküman; **AWS Bedrock AI Gateway**, **Otonom Agent Motoru** ve **Altyapı Güvenlik Standartları**'nın tüm IAM erişim izolasyonunu, veri maskeleme, metrik şifreleme ve kötüye kullanım korumalarını detaylandırır.

---

## 🛡️ 1. Prometheus Metrikleri Güvenlik Zırhı (`/metrics` Authentication)

* **Yetkisiz İfşa Koruması (Anti-Reconnaissance):** Sistem istek hacmi, token harcamaları, hata oranları ve model kullanım istatistiklerinin dış dünyaya sızmasını engellemek için `/metrics` uç noktası **Bearer Token Koruması** ile kilitlenmiştir.
* **Yetkilendirme Kuralı:**
  - `Authorization: Bearer <METRICS_SCRAPE_TOKEN>` veya `x-metrics-token` başlığı zorunludur.
  - Başlık içermeyen tüm istekler `401 Unauthorized` ile otomatik engellenir ve güvenlik loglarına kaydedilir.
* **Prometheus Entegrasyonu:**
  - `monitoring/prometheus.yml` içinde `bearer_token: "bedrock-metrics-secret-token-key-2026"` tanımlanmış olup sadece yetkili izleme konteyneri metrik toplayabilir.

---

## 🔐 2. Sıfır AWS Key İfşası & IAM Least Privilege

1. **Statik Anahtar Kullanılmaz:** Kod tabanında veya ortam değişkenlerinde açıkta `AWS_ACCESS_KEY_ID` veya `AWS_SECRET_ACCESS_KEY` barındırılmaz.
2. **ECS Task Execution Rolü (`BedrockAgentExecutionRole`):** Konteynerler AWS API'lerine minimum yetkili IAM rolleri ile (SigV4) bağlanır:
   - `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`
   - `secretsmanager:GetSecretValue` (Yalnızca `bedrock-gateway-secrets-prod` kaynağı)
   - `logs:CreateLogStream`, `logs:PutLogEvents`
3. **AWS Secrets Manager:** Veritabanı şifreleri, Redis bağlantı dizgisi ve Telegram bot tokeni `bedrock-gateway-secrets-prod` üzerinde şifreli (KMS) saklanır.

---

## 🛡️ 3. AWS Bedrock Guardrails & Hassas Veri Maskeleme (PII)

1. **PII Maskeleme (Anonymization):**
   - Kullanıcıların sohbetlerinde veya dokümanlarında geçen Kredi Kartı numaraları, Telefon Numaraları ve E-posta adresleri modele gönderilmeden önce `EnterpriseGuardrailService` tarafından otomatik maskelenir (`[CREDIT_CARD]`, `[PHONE_NUMBER]`, `[EMAIL]`).
2. **Prompt Injection & Jailbreak Koruması:**
   - Sistem direktiflerini çiğnemeye yönelik kötü niyetli komutlar ("Ignore all previous instructions") filtreye takılarak model çağrısı öncesi bloke edilir.

---

## 🔑 4. API Key Güvenliği & Kriptografik SHA-256 Hashing

- **Anahtar Formatı:** `bgk_<random_32_bytes>`
- **Tek Yönlü Hashleme:** Ham API anahtarları veritabanında **asla açık metin (plaintext) tutulmaz.** Sadece SHA-256 kriptografik hash'i (`key_hash`) saklanır.
- **Tek Seferlik Gösterim:** Üretilen anahtar kullanıcıya yalnızca ilk oluşturma anında gösterilir.

---

## 🚦 5. Dağıtık Rate Limiting & DoS Koruması

- **Redis Token Bucket:** Her API anahtarı ve IP adresi için dakikalık hız sınırı (Varsayılan: 120 RPM) uygulanır. Sınır aşıldığında `429 Too Many Requests` döner.
- **Otomatik Gitleaks Taraması:** GitHub Actions CI/CD hattındaki her PR'da otomatik secret taraması yapılır.
