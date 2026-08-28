import time
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, Response, Header, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.database import engine, Base
from app.core.redis import init_redis, close_redis
from app.core.seed import seed_database
from app.core.errors import GatewayAPIException
from app.api.v1 import chat, models, images
from app.api import auth, api_keys, wallet, usage, admin, chat_ui, agents
from loguru import logger


from app.services.scheduler import BackgroundSchedulerService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init Redis, initialize DB tables, seed catalog, start background scheduler
    logger.info("Initializing AWS Bedrock AI Gateway...")
    await init_redis()
    try:
        await seed_database()
    except Exception as e:
        logger.warning(f"Seed database warning: {e}")

    try:
        await BackgroundSchedulerService.start()
    except Exception as e:
        logger.warning(f"Failed to start background scheduler: {e}")

    yield
    # Shutdown
    logger.info("Shutting down Gateway...")
    try:
        await BackgroundSchedulerService.stop()
    except Exception as e:
        logger.warning(f"Error stopping background scheduler: {e}")
    await close_redis()
    await engine.dispose()



app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production AWS Bedrock AI Gateway Platform (OpenRouter Equivalent for AWS Bedrock)",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

from app.core.metrics import PrometheusMiddleware, get_prometheus_metrics

app.add_middleware(PrometheusMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Standard OpenAI Error Envelope Exception Handlers
@app.exception_handler(GatewayAPIException)
async def gateway_api_exception_handler(request: Request, exc: GatewayAPIException):
    headers = {}
    if hasattr(exc, "retry_after") and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers=headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_msg = "; ".join([f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()])
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": f"Validation error: {error_msg}",
                "type": "invalid_request_error",
                "param": None,
                "code": "VALIDATION_ERROR"
            }
        }
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "An unexpected error occurred on the AI Gateway.",
                "type": "internal_error",
                "param": None,
                "code": "INTERNAL_SERVER_ERROR"
            }
        }
    )


# Health check endpoint for ALB / ECS / CloudWatch
@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Bedrock AI Gateway",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics(
    authorization: Optional[str] = Header(None),
    x_metrics_token: Optional[str] = Header(None, alias="x-metrics-token"),
    token: Optional[str] = Query(None)
):
    """
    Secure Prometheus Metrics Scrape Endpoint.
    Requires Bearer Token authentication to prevent reconnaissance and information leakage.
    """
    expected_token = settings.METRICS_SCRAPE_TOKEN
    
    provided_token = None
    if authorization:
        parts = authorization.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            provided_token = parts[1]
        else:
            provided_token = authorization
    elif x_metrics_token:
        provided_token = x_metrics_token
    elif token:
        provided_token = token

    # In non-testing environments, enforce authentication
    if settings.ENVIRONMENT != "test":
        if not provided_token or provided_token != expected_token:
            logger.warning(f"Unauthorized access attempt to /metrics from unauthorized client")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Valid Bearer token required to access system metrics.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    data, content_type = get_prometheus_metrics()
    return Response(content=data, media_type=content_type)



# Include Routers
# OpenAI-Compatible V1 API
app.include_router(chat.router, prefix="/v1", tags=["OpenAI Chat Completions"])
app.include_router(models.router, prefix="/v1", tags=["OpenAI Models"])
app.include_router(images.router, prefix="/v1", tags=["OpenAI Images"])

# Platform & SaaS APIs
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication & MFA"])
app.include_router(api_keys.router, prefix="/api/keys", tags=["API Key Management"])
app.include_router(api_keys.router, prefix="/api/api-keys", tags=["API Key Management Alias"])
app.include_router(wallet.router, prefix="/api/wallet", tags=["Wallet & Stripe Billing"])
app.include_router(usage.router, prefix="/api/usage", tags=["Usage & Analytics"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin & Margins"])
app.include_router(chat_ui.router, prefix="/api/chat-ui", tags=["Dashboard Chat Persistence"])
app.include_router(agents.router, prefix="/api/agents", tags=["AI Agents & Telegram/Email Tools"])
