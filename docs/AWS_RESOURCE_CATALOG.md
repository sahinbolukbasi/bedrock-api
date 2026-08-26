# 🌐 AWS Kaynak Kataloğu & Resource Group Haritası

Tüm platform kaynakları `us-east-1` bölgesinde çalışmakta olup, **AWS Resource Groups** servisi altında `bedrock-gateway-production-resources` grubuyla merkezi olarak yönetilmektedir.

```bash
# Resource Group altındaki tüm kaynakları listeleme komutu:
aws resource-groups list-group-resources --region us-east-1 --group-name "bedrock-gateway-production-resources"
```

---

## 📋 Aktif Kaynak Listesi ve ARN Tablosu

### 1. Compute & Containers (AWS ECS Fargate)
* **Cluster:** `arn:aws:ecs:us-east-1:996270854731:cluster/bedrock-gateway-cluster`
* **Backend Servisi:** `arn:aws:ecs:us-east-1:996270854731:service/bedrock-gateway-cluster/bedrock-gateway-backend-svc`
* **Frontend Servisi:** `arn:aws:ecs:us-east-1:996270854731:service/bedrock-gateway-cluster/bedrock-gateway-frontend-svc`
* **Backend ECR Deposu:** `996270854731.dkr.ecr.us-east-1.amazonaws.com/bedrock-gateway-backend`
* **Frontend ECR Deposu:** `996270854731.dkr.ecr.us-east-1.amazonaws.com/bedrock-gateway-frontend`

### 2. Ağ & Yük Dengeleme (VPC, ALB, Subnets)
* **VPC ID:** `vpc-0d0dae9debcce61a4` (`10.0.0.0/16`)
* **Public Subnets:** `subnet-0be5b4c5b50da1e0d` (us-east-1a), `subnet-0e981219431966ac3` (us-east-1b)
* **Private Subnets:** `subnet-048a14fee60b405b5` (us-east-1b), `subnet-0b12d50e306dad467` (us-east-1a)
* **Application Load Balancer (ALB):** `arn:aws:elasticloadbalancing:us-east-1:996270854731:loadbalancer/app/bedrock-gateway-alb/2ac09b871273b3d6`
  * DNS Adı: `bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com`
* **Backend Target Group:** `arn:aws:elasticloadbalancing:us-east-1:996270854731:targetgroup/bedrock-gateway-backend-tg/457dbc3afd9a32ff` (Port 8000, Health: `/health`)
* **Frontend Target Group:** `arn:aws:elasticloadbalancing:us-east-1:996270854731:targetgroup/bedrock-gateway-frontend-tg/c77a9973af8432a4` (Port 3000, Health: `/`)
* **Security Group:** `sg-01c2770172f51bca4` (Port 80, 8000, 3000, 5432, 6379)

### 3. Veritabanı & Önbellek (RDS & ElastiCache)
* **Amazon RDS PostgreSQL 16:** `arn:aws:rds:us-east-1:996270854731:db:bedrock-gateway-db`
  * Endpoint: `bedrock-gateway-db.cobqqmqcs7xh.us-east-1.rds.amazonaws.com:5432`
  * DB Adı: `bedrock_gateway`
* **Amazon ElastiCache Redis 7:** `arn:aws:elasticache:us-east-1:996270854731:cluster:bedrock-gateway-redis`
  * Endpoint: `bedrock-gateway-redis.hmoplf.0001.use1.cache.amazonaws.com:6379`

### 4. Güvenlik, Gizli Anahtarlar & Depolama
* **AWS Secrets Manager:** `arn:aws:secretsmanager:us-east-1:996270854731:secret:bedrock-gateway-secrets-prod-8ZOYeZ`
  * Gizli Ad: `bedrock-gateway-secrets-prod`
* **S3 Depolama:** `bedrock-gateway-artifacts-prod`
* **CloudWatch Log Grubu:** `/ecs/bedrock-gateway`

### 5. Bildirim & İletişim Servisleri
* **AWS SNS (SMS Bildirimi):** Otonom ajan uyarılarını SMS olarak cep telefonlarına iletir.
* **AWS SES (E-Posta Servisi):** Detaylı AI raporlarını ve hoş geldiniz maillerini gönderir.
