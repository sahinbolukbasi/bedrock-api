# Production AWS Deployment Guide

This guide walks through deploying the **AWS Bedrock AI Gateway Platform** to AWS using Terraform, ECS Fargate, Aurora PostgreSQL, ElastiCache Redis, and CloudFront.

---

## 1. Prerequisites

- AWS CLI v2 configured (`aws configure`)
- Terraform >= 1.5.0
- Docker & Docker Compose
- AWS IAM Administrator access for initial provisioning

---

## 2. Infrastructure Provisioning with Terraform

### Step 1: Initialize Terraform

```bash
cd terraform
terraform init
```

### Step 2: Plan & Validate

```bash
terraform plan -var="aws_region=us-east-1" -var="environment=prod"
```

### Step 3: Apply Infrastructure

```bash
terraform apply -auto-approve -var="aws_region=us-east-1" -var="environment=prod"
```

Terraform will provision:
- Multi-AZ VPC across 2 Availability Zones
- Internet Gateway and NAT Gateway
- Aurora PostgreSQL in isolated database subnets
- ElastiCache Redis cluster in cache subnets
- ECS Fargate Task Execution Role with `bedrock:InvokeModel*` permissions
- Application Load Balancer (ALB) with HTTPS listener
- AWS WAF WebACL attached to ALB

---

## 3. Building & Pushing Docker Images to AWS ECR

```bash
# 1. Authenticate Docker with Amazon ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# 2. Build and tag Backend image
docker build -t bedrock-gateway-backend ./backend
docker tag bedrock-gateway-backend:latest <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/bedrock-gateway-backend:latest
docker push <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/bedrock-gateway-backend:latest

# 3. Build and tag Frontend image
docker build -t bedrock-gateway-frontend ./frontend
docker tag bedrock-gateway-frontend:latest <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/bedrock-gateway-frontend:latest
docker push <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/bedrock-gateway-frontend:latest
```

---

## 4. Environment Variables & Secrets Management

Store secrets securely in AWS Secrets Manager:

```bash
aws secretsmanager create-secret --name /prod/bedrock-gateway/secrets \
  --secret-string '{"SECRET_KEY":"<32_char_secret>","DATABASE_URL":"postgresql+asyncpg://...","STRIPE_SECRET_KEY":"sk_live_...","STRIPE_WEBHOOK_SECRET":"whsec_..."}'
```

---

## 5. Continuous Deployment (CI/CD)

The `.github/workflows/ci.yml` pipeline automatically triggers on push to `main`:
1. Executes unit tests and concurrency race verification.
2. Builds Next.js frontend assets.
3. Builds and pushes production container images to Amazon ECR.
4. Triggers zero-downtime rolling update on AWS ECS Fargate service.
