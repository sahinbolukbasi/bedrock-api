import json
import time
import uuid
import hashlib
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.errors import ModelNotFoundError, GatewayAPIException
from app.api.deps import get_auth_context, AuthContext
from app.domain.schemas import ChatCompletionRequest, ChatCompletionResponse
from app.models.entities import ModelCatalog
from app.providers.router import provider_router
from app.services.credit_service import CreditService
from app.services.usage_service import UsageService
from app.core.metrics import TOKENS_PROCESSED, WALLET_DEBITS
from loguru import logger

router = APIRouter()


@router.post("/chat/completions", response_model=None)
async def create_chat_completion(
    request_body: ChatCompletionRequest,
    raw_request: Request,
    background_tasks: BackgroundTasks,
    auth_ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    OpenAI-Compatible Chat Completions Endpoint.
    Supports both non-streaming and Server-Sent Events (SSE) streaming (`stream: true`).
    """
    start_time = time.time()
    req_id = f"req-{uuid.uuid4().hex}"
    client_ip = raw_request.client.host if raw_request.client else "127.0.0.1"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    # 1. Fetch Model from Catalog
    stmt = select(ModelCatalog).where(
        ModelCatalog.model_id == request_body.model,
        ModelCatalog.is_enabled == True
    )
    res = await db.execute(stmt)
    model_entity = res.scalar_one_or_none()

    if not model_entity:
        # Also check display_name or short aliases
        stmt_alias = select(ModelCatalog).where(
            ModelCatalog.name == request_body.model,
            ModelCatalog.is_enabled == True
        )
        res_alias = await db.execute(stmt_alias)
        model_entity = res_alias.scalar_one_or_none()

    if not model_entity:
        raise ModelNotFoundError(request_body.model)

    # 2. Pre-flight Balance Lock / Check
    # Ensures the user has at least a minimal balance to start generation
    await CreditService.check_and_lock_balance(
        db=db,
        user_id=auth_ctx.user.id,
        required_minimum_usd=0.0005
    )

    # 3. Resolve Model Provider
    provider = provider_router.get_provider(model_entity.provider)

    # 4. Handle Streaming Response (SSE)
    if request_body.stream:
        async def event_generator() -> AsyncGenerator[str, None]:
            accumulated_input_tokens = 0
            accumulated_output_tokens = 0

            try:
                async for chunk, in_tok_delta, out_tok_delta in provider.stream_chat(request_body, model_entity):
                    accumulated_input_tokens += in_tok_delta
                    accumulated_output_tokens += out_tok_delta
                    
                    chunk_json = chunk.model_dump_json(exclude_unset=True)
                    yield f"data: {chunk_json}\n\n"

                # Final OpenAI delimiter
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(f"Error during SSE stream: {e}")
                err_payload = json.dumps({"error": {"message": str(e), "type": "stream_error"}})
                yield f"data: {err_payload}\n\n"
                yield "data: [DONE]\n\n"

            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                # Meter usage and charge wallet in async background
                try:
                    # Note: We create a fresh DB session for background task
                    from app.core.database import AsyncSessionLocal
                    async with AsyncSessionLocal() as bg_db:
                        await UsageService.record_and_charge_usage(
                            db=bg_db,
                            request_id=req_id,
                            user_id=auth_ctx.user.id,
                            model_entity=model_entity,
                            input_tokens=accumulated_input_tokens or 20,
                            output_tokens=accumulated_output_tokens or 10,
                            duration_ms=duration_ms,
                            api_key_id=auth_ctx.api_key.id if auth_ctx.api_key else None,
                            ip_hash=ip_hash
                        )
                except Exception as ex:
                    logger.error(f"Failed to record usage for stream {req_id}: {ex}")

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Request-ID": req_id
            }
        )

    # 5. Handle Non-Streaming Response
    response, in_tokens, out_tokens = await provider.generate_chat(request_body, model_entity)
    duration_ms = int((time.time() - start_time) * 1000)

    # Record usage & atomically charge wallet
    usage_rec = await UsageService.record_and_charge_usage(
        db=db,
        request_id=req_id,
        user_id=auth_ctx.user.id,
        model_entity=model_entity,
        input_tokens=in_tokens,
        output_tokens=out_tokens,
        duration_ms=duration_ms,
        api_key_id=auth_ctx.api_key.id if auth_ctx.api_key else None,
        ip_hash=ip_hash
    )

    TOKENS_PROCESSED.labels(model_id=model_entity.model_id, token_type="prompt").inc(in_tokens)
    TOKENS_PROCESSED.labels(model_id=model_entity.model_id, token_type="completion").inc(out_tokens)
    WALLET_DEBITS.labels(model_id=model_entity.model_id).inc(float(usage_rec.customer_charged_usd))

    if response.usage:
        response.usage.cost_usd = usage_rec.customer_charged_usd

    return response
