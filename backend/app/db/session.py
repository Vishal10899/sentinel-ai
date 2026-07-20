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
database_available = create_async_engine is not None
engine: Any = None
if database_available:
    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )

# Request handlers receive isolated sessions and retain control of transactions.
AsyncSessionFactory = (
    async_sessionmaker(engine, expire_on_commit=False) if database_available else None
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped session and safely roll back failed work."""
    if AsyncSessionFactory is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database dependency is not installed",
        )
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
