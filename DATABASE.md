# Database Architecture & PostgreSQL Schema

This document details the PostgreSQL 16 schema, data types, indexes, and transactional locking mechanics for the **AWS Bedrock AI Gateway Platform**.

---

## 1. Schema Diagram

```
users (id, email, hashed_password, role, is_active)
  ├── user_sessions (id, user_id, token_hash, expires_at)
  ├── api_keys (id, user_id, prefix, hashed_secret, spending_limit_usd)
  ├── wallets (id, user_id, balance_usd, version)
  │     └── wallet_transactions (id, wallet_id, amount_usd, type, idempotency_key)
  ├── credit_purchases (id, user_id, stripe_session_id, amount_usd, status)
  ├── usage_records (id, user_id, model_id, total_tokens, customer_charged_usd)
  ├── conversations (id, user_id, title, model_id)
  │     └── messages (id, conversation_id, role, content, tokens)
  └── audit_logs (id, user_id, action, resource_type, details)

models (id, model_id, provider, name, display_name, type, is_enabled)
  └── model_pricing (id, model_id, customer_input_price_per_1k, margin_percent)
```

---

## 2. Table Definitions & Constraints

### `wallets`
Stores the current cash balance of the user account.
```sql
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    balance_usd NUMERIC(14, 6) NOT NULL DEFAULT 0.000000,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    version INT NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_wallets_user_id ON wallets(user_id);
```

### `wallet_transactions`
Immutable financial ledger of all credit additions, deductions, and refunds.
```sql
CREATE TABLE wallet_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    amount_usd NUMERIC(14, 6) NOT NULL,
    type VARCHAR(50) NOT NULL, -- PURCHASE, USAGE_DEDUCTION, REFUND, BONUS
    reference_id VARCHAR(128),
    balance_after NUMERIC(14, 6) NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_wallet_tx_wallet_id ON wallet_transactions(wallet_id);
CREATE INDEX idx_wallet_tx_idempotency ON wallet_transactions(idempotency_key);
```

### `api_keys`
Hashed API keys for tenant isolation and rate limiting.
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    prefix VARCHAR(16) NOT NULL,
    hashed_secret VARCHAR(128) UNIQUE NOT NULL,
    rate_limit_rpm INT NOT NULL DEFAULT 120,
    spending_limit_usd NUMERIC(14, 4),
    spending_used_usd NUMERIC(14, 4) NOT NULL DEFAULT 0.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_api_keys_hashed_secret ON api_keys(hashed_secret);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
```

### `usage_records`
Detailed per-request token metering and platform profit breakdown.
```sql
CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(128) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE RESTRICT,
    endpoint VARCHAR(128) NOT NULL DEFAULT '/v1/chat/completions',
    input_tokens INT NOT NULL DEFAULT 0,
    output_tokens INT NOT NULL DEFAULT 0,
    total_tokens INT NOT NULL DEFAULT 0,
    provider_cost_usd NUMERIC(14, 6) NOT NULL DEFAULT 0.0,
    customer_charged_usd NUMERIC(14, 6) NOT NULL DEFAULT 0.0,
    platform_profit_usd NUMERIC(14, 6) NOT NULL DEFAULT 0.0,
    duration_ms INT NOT NULL DEFAULT 0,
    status_code INT NOT NULL DEFAULT 200,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_usage_records_user_id ON usage_records(user_id);
CREATE INDEX idx_usage_records_created_at ON usage_records(created_at);
```

---

## 3. High-Concurrency Transaction Strategy

To guarantee race-condition free deductions, every inference request performs a pessimistic lock:

```python
stmt = select(Wallet).where(Wallet.user_id == user_id).with_for_update()
wallet = await db.execute(stmt)
```

This prevents two simultaneous calls from reading the same starting balance, ensuring negative balances are impossible.
