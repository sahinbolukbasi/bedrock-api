# AWS Bedrock AI Gateway Platform

> **OpenRouter-Equivalent AI Gateway & SaaS Platform for AWS Bedrock.**
> Access frontier AI foundation models (Anthropic Claude 3.5 Sonnet, Amazon Nova, Meta Llama 3.3, Amazon Titan) through unified OpenAI-compatible endpoints with metered billing, granular API key controls, and zero AWS credential exposure.

---

## 🌟 Key Platform Features

- **🛡️ Zero AWS Credential Exposure**: Users and frontend apps communicate exclusively with our Gateway via platform-hashed API keys (`sk-live-...`). All backend-to-Bedrock communication uses native AWS IAM roles.
- **⚡ 100% OpenAI SDK Compatible**: Drop-in replacement for OpenAI's Python, Node.js, and HTTP clients (`POST /v1/chat/completions`, `GET /v1/models`, `POST /v1/images/generations`).
- **🌊 Low-Latency Real-Time Streaming**: Server-Sent Events (SSE) streaming with token-by-token delivery, connection lifecycle management, and accurate post-stream credit metering.
- **💰 Atomic Credit & Wallet Engine**: Strict PostgreSQL row-level locking (`SELECT ... FOR UPDATE`) prevents concurrent balance overdrafts during high-frequency parallel inference.
- **📈 Dynamic Model Catalog & Margins**: Separate provider cost, customer pricing, and platform profit margins managed via admin controls.
- **💳 Production Stripe Billing**: Verified webhook signature processing and idempotent credit ledger transactions.
- **🎨 Modern Web Chat Playground**: Open WebUI-inspired dashboard with model switching, parameter tuning (temperature, system prompt), markdown formatting, and copy code buttons.
- **🚀 Production Infrastructure as Code**: Fully modular Terraform scripts for AWS Multi-AZ VPC, ECS Fargate, Aurora PostgreSQL, ElastiCache Redis, and AWS WAF.

---

## 📐 High-Level Architecture

```
User / Developer / SDK
          │
          ▼
   AWS CloudFront (Edge CDN / TLS)
          │
          ▼
   AWS WAF (DDoS, SQLi, XSS, IP Limits)
          │
          ▼
   FastAPI Gateway (ECS Fargate)
   ├── Auth & API Key Validation (SHA-256)
   ├── Sliding Window Rate Limiter (Redis)
   ├── Atomic Wallet Lock & Balance Check (PostgreSQL FOR UPDATE)
   └── Bedrock Converse Provider Abstraction
          │
          ▼
   AWS Bedrock Runtime (IAM Execution Role)
   ├── Anthropic Claude 3.5 Sonnet v2 / Haiku
   ├── Amazon Nova Pro / Lite / Micro
   ├── Meta Llama 3.3 70B Instruct
   └── Amazon Titan Image Generator G1 v2
```

---

## 🚀 Quickstart (Local Development with Docker Compose)

### 1. Clone & Setup Environment

```bash
git clone https://github.com/your-org/bedrock-ai-gateway.git
cd bedrock-ai-gateway
cp .env.example .env
```

### 2. Launch Stack

```bash
docker-compose up -d
```

Services will be accessible at:
- **Web Dashboard & Chat UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI API & OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL Database**: `localhost:5432`
- **Redis Cache**: `localhost:6379`

Default Superadmin credentials:
- **Email**: `admin@bedrockgateway.com`
- **Password**: `AdminPassword123!`

---

## 💻 Using with Official OpenAI SDKs

### Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk-live-your-generated-api-key"
)

response = client.chat.completions.create(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    messages=[
        {"role": "system", "content": "You are a senior software architect."},
        {"role": "user", "content": "Explain AWS Bedrock Gateway architecture."}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Node.js / TypeScript

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:8000/v1",
  apiKey: "sk-live-your-generated-api-key",
});

const stream = await client.chat.completions.create({
  model: "amazon.nova-pro-v1:0",
  messages: [{ role: "user", content: "Write a high-performance Rust worker." }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}
```

---

## 📚 Documentation Index

- 🏛️ [ARCHITECTURE.md](file:///Users/sahinbolukbasi/Development/bedrock/ARCHITECTURE.md) - Deep architectural design and provider abstractions.
- 🔒 [SECURITY.md](file:///Users/sahinbolukbasi/Development/bedrock/SECURITY.md) - DevSecOps, IAM least privilege, and API key protection.
- 📡 [API.md](file:///Users/sahinbolukbasi/Development/bedrock/API.md) - Complete OpenAI-compatible endpoint specifications.
- 🗄️ [DATABASE.md](file:///Users/sahinbolukbasi/Development/bedrock/DATABASE.md) - PostgreSQL schema, indexes, and concurrency locking.
- ☁️ [DEPLOYMENT.md](file:///Users/sahinbolukbasi/Development/bedrock/DEPLOYMENT.md) - Production AWS deployment with Terraform.
- 🛠️ [TROUBLESHOOTING.md](file:///Users/sahinbolukbasi/Development/bedrock/TROUBLESHOOTING.md) - Operational debugging and monitoring guide.
