"""Async SQLAlchemy engine, session factory, and request dependency."""

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import HTTPException, status

try:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
except ImportError:  # Database is optional at startup; its health endpoint reports unavailability.
    AsyncSession = Any
    async_sessionmaker = None
    create_async_engine = None

from app.core.settings import settings


# A reusable async engine owns PostgreSQL connections for the application process.
database_available = create_async_engine is not None and bool(settings.database_url)
engine: Any = None
if database_available:
    engine_kwargs = {"pool_pre_ping": True}
    if "sqlite" not in settings.database_url:
        engine_kwargs["pool_size"] = settings.database_pool_size
        engine_kwargs["max_overflow"] = settings.database_max_overflow

    engine = create_async_engine(
        settings.database_url,
        **engine_kwargs,
    )

# Request handlers receive isolated sessions and retain control of transactions.
AsyncSessionFactory = (
    async_sessionmaker(engine, expire_on_commit=False) if (database_available and engine is not None) else None
)


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async context manager for database sessions outside request dependencies."""
    if AsyncSessionFactory is None or engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is not configured or unavailable",
        )
    session = AsyncSessionFactory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        try:
            await session.rollback()
        except Exception:
            pass
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped database session."""

    if AsyncSessionFactory is None or engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is not configured or unavailable",
        )

    session = AsyncSessionFactory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        try:
            await session.rollback()
        except Exception:
            pass
        await session.close()

