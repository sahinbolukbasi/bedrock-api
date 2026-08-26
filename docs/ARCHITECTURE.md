# 🏛️ AWS Bedrock AI Gateway — Uçtan Uca Mimari

Platform, AWS bulut altyapısı üzerinde kurumsal standartlarda, yüksek erişilebilirliğe (HA) ve otomatik ölçeklenebilirliğe sahip bir yapay zeka ağ geçididir.

---

## 🗺️ Sistem Mimarisi Şeması

```
                       ┌─────────────────────────┐
                       │   Kullanıcı / İstemci   │
                       │  (Tarayıcı / Telegram)  │
                       └────────────┬────────────┘
                                    │
                                    ▼
       ┌───────────────────────────────────────────────────────────┐
       │         AWS Application Load Balancer (ALB)               │
       │         bedrock-gateway-alb-664380835.us-east-1           │
       └─────────────┬───────────────────────────────┬─────────────┘
                     │                               │
       Path: /       │                               │ Path: /api/* , /v1/*
                     ▼                               ▼
       ┌───────────────────────────┐   ┌───────────────────────────┐
       │   ECS Fargate Frontend    │   │    ECS Fargate Backend    │
       │   (Next.js 14 Dashboard)  │   │  (FastAPI Async Gateway)  │
       └───────────────────────────┘   └─────────────┬─────────────┘
                                                     │
                     ┌───────────────────────────────┼───────────────────────────────┐
                     ▼                               ▼                               ▼
       ┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
       │  AWS Bedrock Runtime API  │   │  Amazon RDS PostgreSQL 16 │   │ Amazon ElastiCache Redis  │
       │  (Nova, Claude, Llama 3)  │   │  (Kullanıcı, Cüzdan, Log) │   │ (Rate Limit, Cache, Lock) │
       └───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
                     │
                     ├───────────────────────────────┬───────────────────────────────┐
                     ▼                               ▼                               ▼
       ┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
       │   AWS SNS (SMS Motoru)    │   │  AWS SES (E-Posta Motoru) │   │   AWS Secrets Manager     │
       │   (Telefon Bildirimleri)  │   │   (HTML AI Raporları)     │   │ (Gizli Anahtar Kasası)    │
       └───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
```

---

## 🔒 Güvenlik & Yetkilendirme Prensipleri

1. **IAM Rol Tabanlı Erişim:** ECS servisleri `bedrock-gateway-ecs-task-role` üzerinden AWS Bedrock, Secrets Manager ve CloudWatch yetkilerini otomatik üstlenir; kod içine AWS access key gömülmez.
2. **API Anahtarı Hashleme:** Veritabanında hiçbir API anahtarı düz metin saklanmaz; tüm `sk-live-...` anahtarları SHA-256 hash ile doğrulanır.
3. **MFA / 2FA Desteği:** TOTP standardında iki faktörlü kimlik doğrulama sunulur.
4. **Hız Sınırlama (Rate Limiting):** Redis tabanlı Token Bucket algoritması ile kötüye kullanım ve bot saldırıları engellenir.
