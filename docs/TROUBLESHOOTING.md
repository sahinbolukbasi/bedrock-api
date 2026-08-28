# 🛠️ Sorun Giderme & Olay Müdahale Rehberi (Troubleshooting & Runbook)

Bu doküman; canlı üretim (Production) ortamında karşılaşılabilecek olası altyapı, konteyner, veritabanı ve LLM hatalarına yönelik **adım adım teşhis ve çözüm prosedürlerini** içerir.

---

## 🚨 1. "502 Bad Gateway" veya ALB Yanıt Vermiyor

### Belirti:
Tarayıcıda veya API isteklerinde HTTP 502 Bad Gateway hatası alınması.

### Neden:
AWS Application Load Balancer (ALB), ECS Fargate arkasındaki Backend (`bedrock-gateway-backend-svc`) konteynerinin sağlık kontrolünü (`/health`) geçemediğinde bu hatayı döner.

### Çözüm Adımları:
1. **Target Group Sağlık Durumunu Kontrol Edin:**
   ```bash
   aws elbv2 describe-target-health \
     --target-group-arn $(aws elbv2 describe-target-groups --names bedrock-gateway-backend-tg --query 'TargetGroups[0].TargetGroupArn' --output text) \
     --region us-east-1
   ```
2. **CloudWatch Loglarını Canlı İzleyin:**
   ```bash
   aws logs get-log-events --region us-east-1 --log-group-name /ecs/bedrock-gateway --limit 50
   ```
3. **ECS Servisini Yeniden Başlatın (Zero-Downtime Rolling Update):**
   ```bash
   aws ecs update-service --cluster bedrock-gateway-cluster --service bedrock-gateway-backend-svc --force-new-deployment --region us-east-1
   ```

---

## 🛑 2. AWS Bedrock Kota Aşımı (`ThrottlingException`)

### Belirti:
API yanıtlarında `429 Too Many Requests` veya `ThrottlingException: Rate exceeded` hatası.

### Neden:
AWS hesabındaki ilgili model (örn. Claude 3.7 Sonnet) için Token-Per-Minute (TPM) sınırına ulaşılması.

### Çözüm:
1. Sistemde otomatik **Fallback (Yedek Model)** mekanizması aktiftir; istek otomatik olarak `anthropic.claude-3-5-haiku-20241022-v1:0` veya `amazon.nova-micro-v1:0` modeline yönlendirilir.
2. AWS Service Quotas konsolundan *Bedrock -> Claude 3.7 Sonnet Invocations* kotasını artırma talebi açın.

---

## 📱 3. Telegram Botu Mesajlara Yanıt Vermiyor

### Belirti:
Telegram'dan `/start` veya `/run` yazıldığında bota cevap gelmemesi.

### Çözüm:
1. **Telegram Token'ın Doğruluğunu Test Edin:**
   ```bash
   curl -s "https://api.telegram.org/bot$(aws secretsmanager get-secret-value --secret-id bedrock-gateway-secrets-prod --query SecretString --output text | jq -r .TELEGRAM_BOT_TOKEN)/getMe"
   ```
2. **ECS Telegram Worker'ını Yeniden Başlatın:**
   ```bash
   aws ecs update-service --cluster bedrock-gateway-cluster --service bedrock-gateway-telegram-svc --force-new-deployment --region us-east-1
   ```

---

## 🗄️ 4. RDS PostgreSQL / Redis Bağlantı Zaman Aşımı

### Belirti:
`asyncpg.exceptions.CannotConnectNowError` veya `redis.exceptions.ConnectionError`.

### Çözüm:
1. ECS Security Group'unun (`sg-bedrock-ecs-tasks`) RDS ve Redis Security Group'larına inbound 5432 ve 6379 portlarından erişim izni olduğunu doğrulayın.
2. RDS Multi-AZ failover durumunu kontrol edin:
   ```bash
   aws rds describe-db-instances --db-instance-identifier bedrock-gateway-db --region us-east-1 --query 'DBInstances[0].DBInstanceStatus'
   ```
