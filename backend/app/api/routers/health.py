"""Service health endpoint."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.settings import settings
from app.cache.client import get_redis
from app.db.session import database_available, get_db
from app.providers.manager import provider_manager


# The version prefix is applied when this router is registered in the app.
router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("")
async def health_check() -> dict[str, str]:
    """Return public health metadata without exposing infrastructure details."""
    return {
        "status": "healthy",
        "service": settings.project_title,
        "version": settings.project_version,
    }


@router.get("/database")
async def database_health_check(
    db: Annotated[object, Depends(get_db)],
) -> dict[str, str]:
    """Verify PostgreSQL connectivity without querying application tables."""
    if not database_available:
        return {"status": "unconfigured", "database": "postgresql", "detail": "Database dependency unavailable"}
    from sqlalchemy import text

    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "postgresql"}
    except Exception as error:
        logger.warning("Database health check notice: %s", error)
        return {"status": "degraded", "database": "postgresql", "detail": str(error)}


@router.get("/redis")
async def redis_health_check(
    redis_client: Annotated[object, Depends(get_redis)],
) -> dict[str, str]:
    """Verify Redis connectivity without reading or writing application cache entries."""
    if redis_client is None:
        return {"status": "unconfigured", "redis": "disconnected"}

    try:
        await redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as error:
        logger.warning("Redis health check notice: %s", error)
        return {"status": "degraded", "redis": "disconnected", "detail": str(error)}


@router.get("/providers")
async def providers_health_check() -> dict[str, object]:
    """Report local provider configuration without calling any AI provider APIs."""
    return {"status": "healthy", "providers": await provider_manager.health_checks()}
