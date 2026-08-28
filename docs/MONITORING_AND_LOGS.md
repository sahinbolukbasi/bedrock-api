# 📊 Canlı İzleme, Grafana Dashboard & Metrik Yönetimi

Bedrock AI Gateway ve Otonom Agent sistemi; yüksek performans, düşük gecikme, otonom bot takibi ve güvenlik olaylarının gerçek zamanlı izlenmesi için **Grafana & Prometheus** ile donatılmıştır.

---

## 📈 1. Grafana Dashboard Servisi (`monitoring/`)

Grafana servisi, **3 ana satır (row)** ve **8 gelişmiş panel** ile otomatik olarak yapılandırılmıştır:

### 🚀 Satır 1: AWS Bedrock Gateway — Sistem & Trafik Özeti
1. **Toplam İstek Hızı (RPS):** `sum(rate(gateway_requests_total[1m]))` — Canlı throughput trafiği.
2. **İstek Gecikmesi (Latency p95):** `histogram_quantile(0.95, sum(rate(gateway_request_duration_seconds_bucket[5m])) by (le))` — Yanıt süreleri.
3. **HTTP Durum Kodları Dağılımı:** 2xx Başarılı, 4xx Hatalar, 5xx Sunucu Hataları (Pasta grafik).

### 🤖 Satır 2: Otonom Agent, Hafıza Tasarrufu & Güvenlik
4. **Yürütülen Otonom Görevler:** `sum(gateway_agent_runs_total)` — Başarıyla tamamlanan otonom görevler.
5. **Hafıza & RAG ile Tasarruf Edilen Token:** `sum(gateway_agent_saved_tokens_total)` — 3-Katmanlı hafıza ve yerel RAG ile kurtarılan token hacmi.
6. **🛡️ Bedrock Guardrail Olayları:** `sum(gateway_guardrail_events_total)` — PII maskeleme ve engellenen prompt injection saldırıları.
7. **📱 Telegram Bot Mesajlaşma Hacmi:** `sum(gateway_telegram_messages_total)` — Çift yönlü Telegram bot bildirimleri.

### 💰 Satır 3: AWS Bedrock Modelleri — Token & Maliyet Analizi
8. **Model Bazında İşlenen Token Sayısı:** `sum by (model_id) (rate(gateway_tokens_total[5m]))` — Claude 3.7, Claude 3.5 Haiku ve Nova Micro kullanım grafiği.
9. **Kümülatif Çıkarım Maliyeti ($ USD):** `sum by (model_id) (gateway_cost_usd_total)` — Model bazlı toplam AWS faturası.

---

## 🛠️ 2. Grafana İzleme Servisini Başlatma (Port 3001)

```bash
# Docker ile Grafana Observability Konteynerini Başlatma
docker build -t bedrock-grafana ./monitoring
docker run -d -p 3001:3000 --name bedrock-monitoring bedrock-grafana
```
* **Erişim Adresi:** `http://localhost:3001` (veya ALB üzerinden)
* **Otomatik Yenileme:** Her 5 saniyede bir (Canlı Akış)
* **Kullanıcı / Şifre:** `admin` / `AdminPassword123!`

---

## 📝 3. AWS CloudWatch Log Akışları

Tüm backend ve frontend logları AWS CloudWatch altında toplanır:
* **Log Grubu:** `/ecs/bedrock-gateway`
* **Log İnceleme Komutu:**
```bash
aws logs get-log-events --region us-east-1 --log-group-name /ecs/bedrock-gateway --log-stream-name "$(aws logs describe-log-streams --region us-east-1 --log-group-name /ecs/bedrock-gateway --order-by LastEventTime --descending --limit 1 --query 'logStreams[0].logStreamName' --output text)" --limit 30
```
