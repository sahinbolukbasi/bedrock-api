# 📊 İzleme, Grafana Dashboard & Log Yönetimi

Bedrock AI Gateway, üretim ortamında yüksek performans, düşük gecikme ve sıfır hata garantisi için Prometheus metrikleri, CloudWatch Log Grupları ve Grafana Dashboard servisiyle donatılmıştır.

---

## 📈 Grafana Dashboard Servisi (`monitoring/`)

Grafana servisi, Gateway metriklerini ve AWS CloudWatch loglarını görselleştirmek için hazır şablonlarla yapılandırılmıştır.

### 🛠️ Başlatma Komutu
```bash
# Docker ile Grafana İzleme Servisini Başlatma (Port 3001)
docker build -t bedrock-grafana ./monitoring
docker run -d -p 3001:3000 --name bedrock-monitoring bedrock-grafana
```
* **Erişim Adresi:** `http://localhost:3001` (veya ALB izleme portu)
* **Varsayılan Giriş:** `admin` / `AdminPassword123!`

---

## 🎯 İzlenen Temel Metrikler

1. **İstek Hızı (RPS):** `rate(http_requests_total[1m])`
2. **Gecikme (Latency p95/p99):** `http_request_duration_seconds_bucket`
3. **HTTP Durum Kodları Dağılımı:** 2xx Başarılı, 4xx İstemci Hatası, 5xx Sunucu Hatası
4. **Model Başına Token Tüketimi:** Nova Micro, Nova Lite, Claude 3.5 Sonnet token hızları
5. **AWS Bedrock Maliyet Tahmini ($):** `bedrock_cost_usd_total`
6. **Otonom Ajan Tetiklemeleri:** Cron ile çalışan ajan sayısı, SMS/Telegram bildirim başarı oranı

---

## 📝 CloudWatch Log Akışları

Tüm ECS backend ve frontend logları AWS CloudWatch altında toplanır:
* **Log Grubu:** `/ecs/bedrock-gateway`
* **Log Okuma Komutu:**
```bash
aws logs get-log-events --region us-east-1 --log-group-name /ecs/bedrock-gateway --log-stream-name "$(aws logs describe-log-streams --region us-east-1 --log-group-name /ecs/bedrock-gateway --order-by LastEventTime --descending --limit 1 --query 'logStreams[0].logStreamName' --output text)" --limit 30
```
