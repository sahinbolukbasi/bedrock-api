# 🛠️ Sistem Hata Ayıklama & Sorun Giderme Kılavuzu (Troubleshooting)

Bu doküman, AWS Bedrock AI Gateway sisteminde karşılaşılabilecek olası aksaklıklar için adım adım çözüm yöntemlerini içerir.

---

## 1. 502 Bad Gateway veya Backend Bağlantı Hatası

### Nedenler:
1. ECS Fargate backend container başlatma sırasında çöküyor (Örn: Python import hatası, eksik modül).
2. ALB Target Group health check (`GET /health`) başarısız oluyor.

### Çözüm Adımları:
```bash
# 1. En son CloudWatch log akışını bulun:
aws logs describe-log-streams --region us-east-1 --log-group-name /ecs/bedrock-gateway --order-by LastEventTime --descending --limit 1 --query "logStreams[0].logStreamName" --output text

# 2. Hata loglarını görüntüleyin:
aws logs get-log-events --region us-east-1 --log-group-name /ecs/bedrock-gateway --log-stream-name "<STREAM_NAME>" --limit 50

# 3. Target Group sağlık durumunu kontrol edin:
aws elbv2 describe-target-health --region us-east-1 --target-group-arn arn:aws:elasticloadbalancing:us-east-1:996270854731:targetgroup/bedrock-gateway-backend-tg/457dbc3afd9a32ff
```

---

## 2. Bedrock Model Çağrısı "AccessDenied" veya "ThrottlingException" Veriyor

### Nedenler:
- Model seçilen bölgede (`us-east-1`) AWS Bedrock model erişimine açık değil veya kota aşımı var.

### Çözüm:
- `backend/app/providers/bedrock.py` içerisindeki dayanıklı (resilient) model fallback devrededir; `amazon.nova-micro-v1:0` veya `anthropic.claude-3-haiku-20240307-v1:0` modelleri otomatik olarak devreye girer.

---

## 3. Telegram Botu `@BedrocksAiBot` Yanıt Vermiyor

### Nedenler:
- Polling daemon süreci durmuş olabilir veya token Secrets Manager'da eksik olabilir.

### Çözüm:
```bash
# 1. Secrets Manager token kontrolü:
aws secretsmanager get-secret-value --region us-east-1 --secret-id bedrock-gateway-secrets-prod --query SecretString --output text

# 2. Bot daemon'ı yeniden başlatma:
./venv/bin/python -m telegram_bot.bot
```
