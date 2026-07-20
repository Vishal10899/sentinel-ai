"""Application lifecycle hooks for process-level concerns."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.cache.client import close_redis, connect_redis
from app.core.settings import settings
from app.db.session import engine
from app.providers import provider_manager, register_configured_providers


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Log lifecycle events and release shared infrastructure resources."""
    logger.info("Starting %s version %s", settings.project_title, settings.project_version)
    provider_manager.clear()
    register_configured_providers(provider_manager, settings)
    logger.info("Registered provider framework adapters")
    await connect_redis()
    try:
        yield
    finally:
        # Redis is optional infrastructure, so cleanup is safe when unavailable.
        try:
            await close_redis()
        finally:
            # Dispose idle PostgreSQL connections when the application process exits.
            if engine is not None:
                await engine.dispose()
        logger.info("Stopping %s", settings.project_title)
