from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time

# Prometheus Metrics Definitions
REQUEST_COUNT = Counter(
    "gateway_requests_total",
    "Total HTTP and AI Gateway requests processed",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "gateway_request_duration_seconds",
    "Latency of AI Gateway requests in seconds",
    ["endpoint"]
)

TOKENS_PROCESSED = Counter(
    "gateway_tokens_total",
    "Total tokens processed by AI models",
    ["model_id", "token_type"]  # token_type: "prompt" or "completion"
)

WALLET_DEBITS = Counter(
    "gateway_cost_usd_total",
    "Total USD cost charged for AI inference",
    ["model_id"]
)

ACTIVE_INFERENCES = Gauge(
    "gateway_active_inferences",
    "Number of concurrent active inference requests"
)

# Autonomous Agent & Memory Metrics
AGENT_RUNS_TOTAL = Counter(
    "gateway_agent_runs_total",
    "Total autonomous agent tasks executed",
    ["agent_type", "status"]
)

AGENT_SAVED_TOKENS = Counter(
    "gateway_agent_saved_tokens_total",
    "Total tokens saved by 3-layer memory compression & local RAG"
)

GUARDRAIL_EVENTS = Counter(
    "gateway_guardrail_events_total",
    "Total Guardrail security triggers (PII, Prompt Injection)",
    ["event_type"]
)

RAG_QUERIES_TOTAL = Counter(
    "gateway_rag_queries_total",
    "Total Local RAG knowledge queries processed",
    ["source_type"]
)

TELEGRAM_MESSAGES_TOTAL = Counter(
    "gateway_telegram_messages_total",
    "Total Telegram bot messages and notifications",
    ["direction"]
)



class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.time()
        endpoint = request.url.path
        
        # Group parameterized routes
        if endpoint.startswith("/v1/chat/completions"):
            endpoint = "/v1/chat/completions"
        elif endpoint.startswith("/v1/models"):
            endpoint = "/v1/models"
        elif endpoint.startswith("/api/"):
            endpoint = "/api/" + endpoint.split("/")[2] if len(endpoint.split("/")) > 2 else endpoint

        response = await call_next(request)
        duration = time.time() - start_time
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
        
        return response


def get_prometheus_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
