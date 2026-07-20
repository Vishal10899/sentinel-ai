"""Async Redis client lifecycle and request dependency."""

import logging
from typing import Any

from fastapi import HTTPException, status

try:
    import redis.asyncio as redis
    from redis.exceptions import RedisError
except ImportError:  # Allows the API to start when optional infrastructure is absent.
    redis = None
    RedisError = Exception

from app.core.settings import settings


logger = logging.getLogger(__name__)
_redis_client: Any = None


async def connect_redis() -> None:
    """Connect to Redis at startup without preventing the API from starting."""
    global _redis_client

    if _redis_client is not None:
        return
    if redis is None:
        logger.warning("Redis dependency is not installed; continuing without it")
        return

    client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        await client.ping()
    except RedisError as error:
        await client.aclose()
        logger.warning("Redis is unavailable at startup; continuing without it", exc_info=error)
        return

    _redis_client = client
    logger.info("Redis connection established")


async def close_redis() -> None:
    """Close the shared Redis connection gracefully during application shutdown."""
    global _redis_client

    if _redis_client is None:
        return

    client = _redis_client
    _redis_client = None
    try:
        await client.aclose()
    except RedisError as error:
        logger.warning("Redis connection closed with an error", exc_info=error)
    else:
        logger.info("Redis connection closed")


async def get_redis() -> Any:
    """Provide the initialized Redis client or return a clear service-unavailable error."""
    if _redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis unavailable",
        )

    return _redis_client
