# 🚀 Production AWS Deployment Guide

This guide walks through deploying the **AWS Bedrock AI Gateway Platform** to AWS using Terraform, ECS Fargate, Amazon RDS PostgreSQL, Amazon ElastiCache Redis, Application Load Balancers, and AWS Secrets Manager.

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

Terraform provisions:
- Multi-AZ VPC across 2 Availability Zones (`us-east-1a`, `us-east-1b`)
- Internet Gateway and NAT Gateway with Elastic IP
- Amazon RDS PostgreSQL 16 in isolated private database subnets
- Amazon ElastiCache Redis 7 cluster in cache subnets
- ECS Fargate Task Execution Role with `bedrock:InvokeModel*` permissions
- Application Load Balancer (ALB) with path routing rules on Port 80 & 8000
- AWS WAF WebACL attached to ALB

---

## 3. Building & Pushing Docker Images to AWS ECR

```bash
# 1. Authenticate Docker with Amazon ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 996270854731.dkr.ecr.us-east-1.amazonaws.com

# 2. Build and tag Backend image
docker build -t bedrock-gateway-backend ./backend
docker tag bedrock-gateway-backend:latest 996270854731.dkr.ecr.us-east-1.amazonaws.com/bedrock-gateway-backend:latest
docker push 996270854731.dkr.ecr.us-east-1.amazonaws.com/bedrock-gateway-backend:latest

# 3. Build and tag Frontend image
docker build -t bedrock-gateway-frontend ./frontend
docker tag bedrock-gateway-frontend:latest 996270854731.dkr.ecr.us-east-1.amazonaws.com/bedrock-gateway-frontend:latest
docker push 996270854731.dkr.ecr.us-east-1.amazonaws.com/bedrock-gateway-frontend:latest
```

---

## 4. Environment Variables & Secrets Management

Secrets are synchronized dynamically from AWS Secrets Manager (`bedrock-gateway-secrets-prod`):
```bash
aws secretsmanager get-secret-value --region us-east-1 --secret-id bedrock-gateway-secrets-prod --query SecretString --output text
```

---

## 5. Continuous Deployment (CI/CD)

The GitHub Actions workflow (`.github/workflows/ci.yml` and `deploy.yml`) automatically triggers on push to `main`:
1. Executes backend tests and type verification.
2. Builds Next.js 14 frontend assets.
3. Builds and pushes production container images to Amazon ECR.
4. Triggers zero-downtime rolling update on AWS ECS Fargate services (`bedrock-gateway-backend-svc`, `bedrock-gateway-frontend-svc`).
