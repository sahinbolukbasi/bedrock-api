# Troubleshooting & Operations Guide

Operational diagnostics and solutions for common runtime, billing, and provider issues.

---

## 1. AWS Bedrock Invocation Errors

### Problem: `AccessDeniedException` or `UnrecognizedClientException`
- **Cause**: The IAM task execution role lacks permissions to invoke the specific foundation model or the model has not been enabled in the AWS Bedrock console for that AWS region.
- **Solution**:
  1. Open AWS Bedrock Console -> Model Access -> Enable Anthropic Claude 3.5 / Amazon Nova.
  2. Verify IAM Policy includes:
     ```json
     {
       "Effect": "Allow",
       "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
       "Resource": "*"
     }
     ```

### Problem: `ThrottlingException` / Rate Limit Hit
- **Cause**: Upstream AWS Bedrock account quotas exceeded.
- **Solution**: Increase AWS Bedrock quotas in AWS Service Quotas console, or adjust local rate limits in `api_keys.rate_limit_rpm`.

---

## 2. Wallet & Concurrency Issues

### Problem: `HTTP 402 Insufficient Credits`
- **Cause**: User's wallet balance has dropped below the minimum reservation threshold ($0.0005) or the required cost for the image generation request.
- **Solution**:
  - Purchase credits via dashboard `/billing`.
  - In development, trigger the fast-fund endpoint: `POST /api/wallet/dev-fund`.

### Problem: Database Lock Contention on High Concurrency
- **Cause**: Excessive parallel requests for the exact same user ID trying to lock `SELECT ... FOR UPDATE`.
- **Solution**: Ensure connection pool size in `backend/app/core/database.py` has adequate headroom (`pool_size=20`, `max_overflow=10`).

---

## 3. Stripe Webhook Verification Failures

### Problem: `400 Invalid Stripe-Signature`
- **Cause**: The `STRIPE_WEBHOOK_SECRET` environment variable does not match the signing secret provided in the Stripe dashboard for this endpoint.
- **Solution**: Check Stripe Dashboard -> Developers -> Webhooks -> Signing secret (`whsec_...`) and update `.env`.

---

## 4. Health Checks

- Check backend API readiness: `GET http://localhost:8000/health`
- Check active Redis connection: `redis-cli ping` (returns `PONG`)
- View real-time container logs: `docker-compose logs -f backend`
