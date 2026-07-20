"""SQLAlchemy declarative base shared by future persistence models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class that exposes metadata to Alembic without defining any tables."""
