"""Application lifecycle hooks for process-level concerns."""

import asyncio
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.cache.client import close_redis, connect_redis
from app.core.settings import settings
from app.db.session import engine
from app.providers import provider_manager, register_configured_providers

logger = logging.getLogger(__name__)


def _run_alembic_migrations() -> None:
    """Execute Alembic migrations if configured."""
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database schema migrations verified and applied")
    except Exception as error:
        logger.warning("Automated startup migration skipped/failed: %s", error)


async def _init_db_tables() -> None:
    """Ensure database tables and default records exist on startup within event loop."""
    try:
        from app.db.session import engine
        from app.db.base import Base
        import app.models  # Register models with Base.metadata

        if engine is not None:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                from sqlalchemy import text
                await conn.execute(text("""
                    INSERT INTO users (id, name, email, salt, password_hash, created_at, updated_at)
                    VALUES ('default_user', 'System User', 'system@sentinel.ai', 'salt', 'hash', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO NOTHING;
                """))
                await conn.execute(text("""
                    INSERT INTO workspaces (id, name, slug, owner_id, is_active, created_at, updated_at)
                    VALUES ('default', 'Default Workspace', 'default', 'default_user', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO NOTHING;
                """))
            logger.info("Base metadata schema sync and default workspace verification completed")
    except Exception as err:
        logger.warning("Metadata table sync warning: %s", err)


def _seed_demo_data() -> None:
    try:
        from scripts.seed_demo_data import main as seed_main
        seed_main()
    except Exception as err:
        logger.warning("Startup demo data seed warning: %s", err)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Log lifecycle events and release shared infrastructure resources."""
    logger.info("Starting %s version %s", settings.project_title, settings.project_version)
    await asyncio.to_thread(_run_alembic_migrations)
    await _init_db_tables()
    provider_manager.clear()
    register_configured_providers(provider_manager, settings)
    logger.info("Registered provider framework adapters")
    await asyncio.to_thread(_seed_demo_data)
    await connect_redis()
    try:
        yield
    finally:
        try:
            await close_redis()
        finally:
            if engine is not None:
                await engine.dispose()
        logger.info("Stopping %s", settings.project_title)

