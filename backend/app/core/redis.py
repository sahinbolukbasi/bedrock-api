import time
from typing import Optional, Tuple
import redis.asyncio as aioredis
from app.core.config import settings
from loguru import logger

redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> Optional[aioredis.Redis]:
    global redis_client
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=2.0
        )
        await redis_client.ping()
        logger.info("Connected to Redis successfully.")
        return redis_client
    except Exception as e:
        logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}. In-memory fallback will be used.")
        redis_client = None
        return None


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed.")


class RateLimiter:
    """
    Sliding window rate limiter backed by Redis sorted sets (ZSET).
    Gracefully falls back to allowing requests if Redis is unavailable.
    """

    @staticmethod
    async def check_rate_limit(
        key: str,
        max_requests: int = 120,
        window_seconds: int = 60
    ) -> Tuple[bool, int, int]:
        """
        Returns: (allowed: bool, current_count: int, retry_after_seconds: int)
        """
        if not redis_client:
            return True, 1, 0  # Allow in offline/test mode without redis

        now = time.time()
        window_start = now - window_seconds
        redis_key = f"rate_limit:{key}"

        try:
            pipe = redis_client.pipeline()
            # 1. Remove timestamps older than window
            pipe.zremrangebyscore(redis_key, 0, window_start)
            # 2. Count requests in current window
            pipe.zcard(redis_key)
            # 3. Add current timestamp
            pipe.zadd(redis_key, {str(now): now})
            # 4. Set TTL on the key
            pipe.expire(redis_key, window_seconds + 5)
            
            results = await pipe.execute()
            current_count = results[1]

            if current_count >= max_requests:
                # Get oldest element in window to calculate exact retry-after
                oldest = await redis_client.zrange(redis_key, 0, 0, withscores=True)
                retry_after = int(window_seconds - (now - oldest[0][1])) if oldest else window_seconds
                return False, current_count, max(1, retry_after)

            return True, current_count + 1, 0
        except Exception as e:
            logger.error(f"Rate limit check failed for {key}: {e}")
            return True, 1, 0  # Fail open in transient Redis errors

    @staticmethod
    async def track_concurrent_start(key: str, max_concurrent: int = 10) -> bool:
        """Track in-flight concurrent generations."""
        if not redis_client:
            return True
        redis_key = f"concurrent:{key}"
        try:
            count = await redis_client.incr(redis_key)
            await redis_client.expire(redis_key, 300)  # Auto-expire after 5 min
            if count > max_concurrent:
                await redis_client.decr(redis_key)
                return False
            return True
        except Exception:
            return True

    @staticmethod
    async def track_concurrent_end(key: str):
        """Release concurrent request slot."""
        if not redis_client:
            return
        redis_key = f"concurrent:{key}"
        try:
            val = await redis_client.decr(redis_key)
            if val < 0:
                await redis_client.set(redis_key, 0)
        except Exception:
            pass
