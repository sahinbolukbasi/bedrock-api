# API Reference & Endpoints

Complete specifications for the **OpenAI-Compatible AWS Bedrock AI Gateway API**.

---

## 1. Authentication

All requests to `/v1/*` must include a valid API key in the `Authorization` header:

```http
Authorization: Bearer sk-live-xxxxxxxxxxxxxxxxxxxx
```

Dashboard session requests use a standard JWT Bearer token obtained from `/api/auth/login`.

---

## 2. Chat Completions

### `POST /v1/chat/completions`

Creates a model response for the given chat conversation. Supports both standard responses and real-time streaming.

#### Request Body
```json
{
  "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Hello Bedrock!"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 4096,
  "stream": false
}
```

#### Non-Streaming Response (`stream: false`)
```json
{
  "id": "chatcmpl-bedrock-9b2f4c3a",
  "object": "chat.completion",
  "created": 1724678400,
  "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I assist you with AWS Bedrock today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 12,
    "total_tokens": 27,
    "cost_usd": 0.000270
  }
}
```

#### Streaming Response (`stream: true`)
Returns a stream of Server-Sent Events (SSE):

```http
data: {"id":"chatcmpl-bedrock-9b2f4c3a","object":"chat.completion.chunk","created":1724678400,"model":"anthropic.claude-3-5-sonnet-20241022-v2:0","choices":[{"index":0,"delta":{"content":"Hello"}}]}

data: {"id":"chatcmpl-bedrock-9b2f4c3a","object":"chat.completion.chunk","created":1724678400,"model":"anthropic.claude-3-5-sonnet-20241022-v2:0","choices":[{"index":0,"delta":{"content":"!"}}]}

data: [DONE]
```

---

## 3. Model Catalog

### `GET /v1/models`

Lists all enabled models and their pricing structures.

#### Response
```json
{
  "object": "list",
  "data": [
    {
      "id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
      "object": "model",
      "created": 1724678400,
      "owned_by": "bedrock",
      "name": "Anthropic Claude 3.5 Sonnet v2",
      "context_window": 200000,
      "type": "CHAT",
      "capabilities": {
        "vision": true,
        "tools": true,
        "streaming": true
      },
      "pricing": {
        "input_per_1k": 0.0036,
        "output_per_1k": 0.0180
      }
    }
  ]
}
```

---

## 4. Image Generation

### `POST /v1/images/generations`

Generates images using Amazon Titan Image Generator G1 v2 on AWS Bedrock.

#### Request Body
```json
{
  "prompt": "Cyberpunk cityscape with neon lights in high resolution",
  "model": "amazon.titan-image-generator-v2:0",
  "n": 1,
  "size": "1024x1024"
}
```

#### Response
```json
{
  "created": 1724678400,
  "data": [
    {
      "b64_json": "iVBORw0KGgoAAAANSUhEUg...",
      "url": "https://images.bedrockgateway.com/demo-9b2f4c3a.png"
    }
  ],
  "cost_usd": 0.0500
}
```

---

## 5. Standard Error Envelopes

All errors return standard OpenAI JSON error envelopes:

```json
{
  "error": {
    "message": "Your wallet has insufficient credit balance. Please purchase credits to continue.",
    "type": "insufficient_credits",
    "param": null,
    "code": "INSUFFICIENT_CREDITS"
  }
}
```

Common Error Codes:
- `INVALID_API_KEY` (401)
- `FORBIDDEN` (403)
- `MODEL_NOT_FOUND` (404)
- `INSUFFICIENT_CREDITS` (402)
- `RATE_LIMIT_EXCEEDED` (429)
- `UPSTREAM_PROVIDER_ERROR` (502)
