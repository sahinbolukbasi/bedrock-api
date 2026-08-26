# Security & DevSecOps Specification

This document details the security controls, authentication mechanisms, IAM isolation, and abuse protections implemented across the **AWS Bedrock AI Gateway Platform**.

---

## 1. Zero AWS Key Exposure & IAM Least Privilege

1. **No Static Credentials**: The platform does **not** distribute or require AWS Access Key IDs or Secret Access Keys to end users.
2. **IAM Task Execution Role**: Backend services running on AWS ECS Fargate assume an IAM task role with strictly scoped permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel",
           "bedrock:InvokeModelWithResponseStream"
         ],
         "Resource": "*"
       }
     ]
   }
   ```
3. **No Administrative IAM Capabilities**: The ECS task role cannot modify IAM policies, provision resources, or access unauthorized S3 buckets.

---

## 2. API Key Security & Storage

- **Prefix + Secret Format**: Keys are generated as `sk-live-<8_char_prefix><32_char_secret>`.
- **One-Way SHA-256 Hashing**: Full secret keys are **never** stored plaintext in the database. Only the SHA-256 hash (`hashed_secret`) and public prefix are persisted.
- **One-Time Display**: Raw keys are only shown to the user upon initial creation in the dashboard modal.
- **Instant Revocation**: Revoked keys are rejected immediately in-flight.

---

## 3. Rate Limiting & Distributed Abuse Protection

1. **Redis Sliding Window**:
   - Each API key and IP address is metered using Redis sorted sets (ZSET).
   - Exceeding the rate limit returns `HTTP 429 Too Many Requests` with a `Retry-After` header.
2. **AWS WAF (Web Application Firewall)**:
   - Regional WAF WebACL placed in front of CloudFront / Application Load Balancer.
   - Blocks SQL injection (`AWSManagedRulesSQLiRuleSet`), Cross-Site Scripting, and volumetric IP floods (>2000 req/5 min).

---

## 4. Payment Security & Webhook Idempotency

- **Cryptographic Signature Verification**: Stripe webhook events are rejected unless signed with the valid `STRIPE_WEBHOOK_SECRET`.
- **Idempotency Guarantee**: Each payment event stores `idempotency_key = stripe_session_id`. Duplicate webhook deliveries never trigger double-crediting.
- **Client Disconnect Resilience**: SSE streams that disconnect prematurely are caught in the `finally` block to ensure token usage is calculated and recorded accurately.

---

## 5. Multi-Tenant Isolation & Audit Logging

- **Strict Tenant Boundaries**: Database queries enforce `user_id = current_user.id` on all session, API key, conversation, and wallet operations.
- **Admin Audit Trail**: Every sensitive operation (user suspension, model margin modification, API key revocation) writes an immutable record to the `audit_logs` table recording `who`, `what`, `target_id`, `ip_address`, and timestamp.
