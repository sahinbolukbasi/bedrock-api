<div align="center">

# ⚡ AWS Bedrock AI Gateway

### **The Enterprise OpenRouter for AWS Bedrock & Autonomous Multi-Channel AI Agents**

An enterprise-grade, high-throughput, ultra-low latency AI Gateway that unifies **AWS Bedrock foundation models** (Amazon Nova, Anthropic Claude 3.5, Meta Llama 3.3, Mistral Large) into a single standard **OpenAI-compatible `/v1` API**. Features an **Autonomous Bot Execution Engine**, **Self-Improving Memory (Reflection Cache)**, **Multi-Channel Alert Dispatch (Telegram, SMS via SNS, Email via SES)**, and **Grafana Observability**.

[![AWS Bedrock](https://img.shields.io/badge/AWS-Amazon%20Bedrock-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2%20App%20Router-000000?logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20Aurora%20RDS-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7%20ElastiCache-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage%20Container-2496ED?logo=docker&logoColor=white)](https://www.docker.com)
[![Telegram Bot](https://img.shields.io/badge/Telegram-@BedrocksAiBot-2CA5E0?logo=telegram&logoColor=white)](https://t.me/BedrocksAiBot)
[![Grafana](https://img.shields.io/badge/Observability-Grafana%20%26%20Prometheus-F46800?logo=grafana&logoColor=white)](https://grafana.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

[🌐 Live Web Portal](http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com) • [🤖 Telegram Bot](https://t.me/BedrocksAiBot) • [📚 Full Documentation (docs/)](docs/README.md) • [📊 Grafana Monitoring](monitoring/) • [🔒 Security & DevSecOps](docs/SECURITY.md)

</div>

---

## 🌟 Key Platform Capabilities

```
                               ┌─────────────────────────────────────────┐
                               │       AWS Application Load Balancer     │
                               │        (Port 80 Path Routing & WAF)     │
                               └────────────┬────────────────────────────┘
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
┌──────────────────────────────┐                         ┌──────────────────────────────┐
│     Next.js 14 Dashboard     │                         │   FastAPI AI Gateway Core    │
│  • Modern Glassmorphism UI   │                         │  • OpenAI /v1 Proxy API      │
│  • Developer API Key Hub     │                         │  • Distributed Token Bucket  │
│  • Autonomous Agents Studio  │                         │  • Stripe Metered Billing    │
│  • Real-time SSE Chat Studio │                         │  • Voice Synthesis & Audio   │
└──────────────────────────────┘                         └──────────────┬───────────────┘
                                                                        │
        ┌────────────────────────────────┬──────────────────────────────┼──────────────────────────────┐
        ▼                                ▼                              ▼                              ▼
┌───────────────┐               ┌────────────────┐             ┌────────────────┐             ┌────────────────┐
│  AWS Bedrock  │               │ Amazon RDS PG  │             │  ElastiCache   │             │ AWS Notification│
│ Runtime (API) │               │  PostgreSQL 16 │             │  Redis 7 Cache │             │  Dispatch Engine│
│ • Nova Micro  │               │ • User Wallets │             │ • Rate Limiting│             │ • Telegram Bot │
│ • Nova Lite   │               │ • API Key Hash │             │ • Session Cache│             │ • SMS (AWS SNS)│
│ • Claude 3.5  │               │ • Agent Logs   │             │ • Lock Engine  │             │ • Mail (AWS SES)│
│ • Llama 3.3   │               │ • Conversations│             │ • Quota Engine │             │ • Memory Cache │
└───────────────┘               └────────────────┘             └────────────────┘             └────────────────┘
```

### 1. ⚡ 100% OpenAI-Compatible Gateway (`/v1/chat/completions`)
* Seamless drop-in replacement for OpenAI SDKs (`python`, `nodejs`, `csharp`, `golang`, `curl`).
* Real-time Server-Sent Events (SSE) token streaming with zero-buffering response chunks.
* Multimodal support: text generation, vision analysis, and audio speech synthesis.

### 2. 🧠 Autonomous Bot & Agent Execution Platform
* **Cron Scheduling:** Define autonomous background bots with custom schedules (Hourly `0 * * * *`, Daily `0 9 * * *`, Weekly).
* **Self-Improving Memory (Reflection Cache):** Agents distill key insights from every run and automatically append them to their `learned_memory_cache`, improving intelligence over time with **zero fine-tuning costs**.
* **Multi-Channel Dispatch:** Dispatches AI execution reports across:
  * 📱 **Telegram Bot / Webhook:** Instant updates sent directly to Telegram channels or DMs.
  * 📟 **SMS (AWS SNS):** High-priority alerts delivered directly to mobile phones.
  * ✉️ **Email (AWS SES):** Rich HTML analytical summaries delivered to inboxes.

### 3. 🤖 Dedicated Telegram Bot Daemon (`@BedrocksAiBot`)
* Connects via dedicated async long-polling daemon (`telegram_bot/`).
* Instant user onboarding: users authenticate with `/auth sk-live-...` to link their Gateway wallet.
* Interactive commands: `/chat`, `/models`, `/agents`, `/run`, `/balance`.
* Token and secret protection managed dynamically through **AWS Secrets Manager**.

### 4. 💸 Ultra-Low Cost Model Catalog
| Model Name | Model ID | Context | Input Cost / 1k | Output Cost / 1k | Best For |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Amazon Nova Micro** | `amazon.nova-micro-v1:0` | 128k | **$0.000035** | **$0.000140** | 24/7 background bots, sentiment, classification |
| **Amazon Nova Lite** | `amazon.nova-lite-v1:0` | 300k | **$0.000080** | **$0.000320** | High-throughput chat, summarization, low latency |
| **Amazon Nova Pro** | `amazon.nova-pro-v1:0` | 300k | **$0.000800** | **$0.003200** | Multimodal analysis, complex reasoning |
| **Anthropic Claude 3 Haiku** | `anthropic.claude-3-haiku-20240307-v1:0` | 200k | **$0.000250** | **$0.001250** | Fast reasoning, tool use, concise summaries |
| **Meta Llama 3 8B** | `meta.llama3-8b-instruct-v1:0` | 128k | **$0.000200** | **$0.000200** | Open-weights efficiency, code generation |
| **Anthropic Claude 3.5 Sonnet** | `anthropic.claude-3-5-sonnet-20241022-v2:0` | 200k | **$0.003000** | **$0.015000** | State-of-the-art coding, complex math & vision |

---

## 🚀 Quickstart Guide

### 🐍 Python (Standard `openai` SDK)

```python
from openai import OpenAI

# Connect to Bedrock Gateway ALB
client = OpenAI(
    base_url="http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com/v1",
    api_key="sk-live-your-generated-gateway-key"
)

response = client.chat.completions.create(
    model="amazon.nova-micro-v1:0",  # Ultra-low cost: $0.000035 / 1k
    messages=[
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Explain AWS Bedrock in one paragraph."}
    ],
    temperature=0.7
)

print(response.choices[0].message.content)
```

### ⚡ Node.js / TypeScript

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com/v1",
  apiKey: "sk-live-your-generated-gateway-key",
});

async function main() {
  const stream = await client.chat.completions.create({
    model: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    messages: [{ role: "user", content: "Write a high-performance Redis rate limiter in TypeScript." }],
    stream: true,
  });

  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || "");
  }
}

main();
```

### 📡 cURL / HTTP

```bash
curl -X POST http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-live-your-key" \
  -d '{
    "model": "amazon.nova-lite-v1:0",
    "messages": [{"role": "user", "content": "Merhaba!"}],
    "stream": false
  }'
```

---

## 📊 Observability & Monitoring with Grafana

The platform includes a dedicated **Grafana Observability Stack** ([`monitoring/`](monitoring/)) pre-configured with real-time dashboards:

```bash
# Launch Grafana Observability Dashboard
docker build -t bedrock-grafana ./monitoring
docker run -d -p 3001:3000 --name bedrock-monitoring bedrock-grafana
```
* **Dashboard URL:** `http://localhost:3001` (Credentials: `admin` / `AdminPassword123!`)
* **Metrics Tracked:** Realtime RPS, p95/p99 Latency, 2xx/4xx/5xx Distribution, Bedrock Token Consumption, Cost Estimation ($), and CloudWatch `/ecs/bedrock-gateway` log streams.

---

## 🏛️ Enterprise AWS Infrastructure & Resource Group

All production resources are centrally managed in AWS region `us-east-1` under the **AWS Resource Group**: `bedrock-gateway-production-resources`.

* **Compute:** AWS ECS Fargate Cluster (`bedrock-gateway-cluster`)
* **Load Balancer:** Multi-AZ Application Load Balancer with Layer-7 path routing rules
* **Database:** Amazon RDS PostgreSQL 16 Multi-AZ
* **Caching & Locking:** Amazon ElastiCache Redis 7
* **Secrets Management:** AWS Secrets Manager (`bedrock-gateway-secrets-prod`)
* **Storage & Logs:** Amazon S3 (`bedrock-gateway-artifacts-prod`) & CloudWatch (`/ecs/bedrock-gateway`)

---

## 📚 Documentation Index (`docs/`)

Explore the comprehensive technical guides in the [`docs/`](docs/README.md) directory:

| Document | Purpose |
| :--- | :--- |
| 🤖 **[AI_AGENT_PLAYBOOK.md](docs/AI_AGENT_PLAYBOOK.md)** | **Master operational playbook for AI assistants & LLMs to safely inspect, modify, and extend the system** |
| 🌐 **[AWS_RESOURCE_CATALOG.md](docs/AWS_RESOURCE_CATALOG.md)** | Complete mapping of all 36+ AWS resources, ARNs, IDs, and VPC routing |
| 🏛️ **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** | End-to-end cloud topology, container architecture, and request lifecycle |
| 📱 **[TELEGRAM_AND_AUTONOMOUS_BOTS.md](docs/TELEGRAM_AND_AUTONOMOUS_BOTS.md)** | Autonomous engine, Cron scheduling, SNS SMS & SES Email, Reflection Cache |
| 📡 **[API_REFERENCE.md](docs/API_REFERENCE.md)** | Complete OpenAI `/v1` and Gateway management API endpoint specifications |
| 🗄️ **[DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)** | PostgreSQL relational models, Redis keyspaces, and entity relationships |
| 📊 **[MONITORING_AND_LOGS.md](docs/MONITORING_AND_LOGS.md)** | Prometheus metrics, CloudWatch log streams, and Grafana dashboard panels |
| 🚀 **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** | Terraform IaC automation, ECR container packaging, ECS rolling deployment |
| 🔒 **[SECURITY.md](docs/SECURITY.md)** | IAM least-privilege, SHA-256 key hashing, Redis token buckets, WAF rules |
| 🛠️ **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** | Playbook for 502 Bad Gateway, health checks, Bedrock quota and throttling |

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
