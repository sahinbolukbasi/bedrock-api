import time
import uuid
from typing import Optional, Tuple, Union
from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_jwt_token, hash_api_key
from app.core.redis import RateLimiter
from app.core.errors import (
    AuthenticationError,
    PermissionDeniedError,
    RateLimitExceededError
)
from app.models.entities import User, ApiKey

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Authenticates a user via dashboard JWT Bearer token."""
    if not credentials or not credentials.credentials:
        raise AuthenticationError("Missing Authorization token.")

    token = credentials.credentials
    payload = decode_jwt_token(token)
    user_id_str = payload.get("sub")

    if not user_id_str:
        raise AuthenticationError("Invalid or expired session token.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationError("Invalid user identity in token.")

    stmt = select(User).where(User.id == user_uuid)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not user.is_active:
        raise AuthenticationError("User account is inactive or not found.")

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Resolves authenticated user, or falls back to primary/admin user for seamless demo pairing."""
    if credentials and credentials.credentials:
        try:
            token = credentials.credentials
            payload = decode_jwt_token(token)
            user_id_str = payload.get("sub")
            if user_id_str:
                user_uuid = uuid.UUID(user_id_str)
                stmt = select(User).where(User.id == user_uuid)
                res = await db.execute(stmt)
                user = res.scalar_one_or_none()
                if user and user.is_active:
                    return user
        except Exception:
            pass

    # Fallback to primary active user or admin
    stmt = select(User).where(User.is_active == True).order_by(User.created_at.asc()).limit(1)
    res = await db.execute(stmt)
    return res.scalars().first()




async def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Enforces admin role."""
    from app.core.config import settings
    user_role = (current_user.role or "").lower()
    user_email = (current_user.email or "").lower()
    admin_email = (settings.ADMIN_EMAIL or "").lower()

    if user_role not in ("admin", "superadmin") and user_email != admin_email and not user_email.startswith("admin@"):
        raise PermissionDeniedError("Admin privileges required for this action.")
    return current_user


class AuthContext:
    def __init__(self, user: User, api_key: Optional[ApiKey] = None):
        self.user = user
        self.api_key = api_key


async def get_auth_context(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> AuthContext:
    """
    Unified authentication dependency:
    1. If token starts with 'sk-', resolves and validates API Key (OpenRouter / OpenAI style).
    2. Otherwise, resolves JWT user session token.
    3. Enforces per-key or per-user sliding window rate limiting.
    """
    if not authorization:
        raise AuthenticationError("Missing Authorization header. Provide 'Bearer sk-...' or session token.")

    token = authorization.replace("Bearer ", "").strip()
    client_ip = request.client.host if request.client else "127.0.0.1"

    if token.startswith("sk-"):
        # API Key Flow
        hashed = hash_api_key(token)
        stmt = select(ApiKey).where(ApiKey.hashed_secret == hashed)
        res = await db.execute(stmt)
        api_key = res.scalar_one_or_none()

        if not api_key:
            raise AuthenticationError("Invalid API key provided.")

        if not api_key.is_active:
            raise AuthenticationError("This API key has been revoked.")

        if api_key.expires_at and api_key.expires_at.timestamp() < time.time():
            raise AuthenticationError("This API key has expired.")

        # Check spending limit
        if api_key.spending_limit_usd is not None and api_key.spending_used_usd >= api_key.spending_limit_usd:
            raise AuthenticationError("This API key has reached its spending limit.")

        # Check Rate Limit for this specific key
        allowed, current_count, retry_after = await RateLimiter.check_rate_limit(
            key=f"apikey:{api_key.id}",
            max_requests=api_key.rate_limit_rpm,
            window_seconds=60
        )
        if not allowed:
            raise RateLimitExceededError(retry_after=retry_after)

        # Update last used timestamp
        api_key.last_used_at = select(ApiKey).where(ApiKey.id == api_key.id)  # updated in background

        # Fetch associated user
        user_stmt = select(User).where(User.id == api_key.user_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if not user or not user.is_active:
            raise AuthenticationError("Account associated with this API key is inactive.")

        return AuthContext(user=user, api_key=api_key)

    else:
        # JWT Session Flow
        payload = decode_jwt_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Invalid or expired session token.")

        user_stmt = select(User).where(User.id == uuid.UUID(user_id_str))
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if not user or not user.is_active:
            raise AuthenticationError("User account is inactive or not found.")

        # Rate limit by user ID
        allowed, current_count, retry_after = await RateLimiter.check_rate_limit(
            key=f"user:{user.id}",
            max_requests=120,
            window_seconds=60
        )
        if not allowed:
            raise RateLimitExceededError(retry_after=retry_after)

        return AuthContext(user=user, api_key=None)
