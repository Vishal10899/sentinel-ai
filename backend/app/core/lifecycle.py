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


async def _bootstrap_super_admins() -> None:
    """Safely bootstrap and reconcile configured platform Super Admin accounts."""
    try:
        from app.db.session import AsyncSessionFactory, get_db_session
        from app.models.user import User
        from app.auth.service import _hash
        from app.rbac import role_repository
        from app.tenancy.repository import tenancy_repository
        from sqlalchemy import select
        import secrets

        admins_to_bootstrap = [
            {
                "email": settings.bootstrap_super_admin_email_1,
                "password": settings.bootstrap_super_admin_password_1,
                "name": settings.bootstrap_super_admin_name_1,
            },
            {
                "email": settings.bootstrap_super_admin_email_2,
                "password": settings.bootstrap_super_admin_password_2,
                "name": settings.bootstrap_super_admin_name_2,
            },
            {
                "email": settings.bootstrap_admin_email,
                "password": settings.bootstrap_admin_password,
                "name": "System Admin",
            },
        ]

        if AsyncSessionFactory is not None:
            async with get_db_session() as session:
                for admin_spec in admins_to_bootstrap:
                    raw_email = admin_spec.get("email")
                    if not raw_email:
                        continue
                    email = raw_email.strip().lower()
                    name = admin_spec.get("name") or "Super Admin"
                    password = admin_spec.get("password")

                    # Check if user exists
                    stmt = select(User).where(User.email == email)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()

                    if user is None and password:
                        # Create new user
                        salt, pwd_hash = _hash(password)
                        user_id = secrets.token_hex(16)
                        user = User(
                            id=user_id,
                            name=name,
                            email=email,
                            salt=salt,
                            password_hash=pwd_hash,
                        )
                        session.add(user)
                        await session.commit()
                        logger.info("Created bootstrap Super Admin account for %s", email)
                    elif user is not None and password:
                        salt, pwd_hash = _hash(password)
                        user.salt = salt
                        user.password_hash = pwd_hash
                        if name:
                            user.name = name
                        session.add(user)
                        await session.commit()
                        logger.info("Reconciled bootstrap Super Admin credentials for %s", email)

                    if user:
                        # Reconcile Super Admin role & membership
                        role_repository.assign_user_role(user.id, "role-super-admin")
                        user_mem = tenancy_repository.get_user_membership(user.id, org_id="org-default")
                        if not user_mem:
                            tenancy_repository.create_membership(
                                org_id="org-default",
                                workspace_id="default",
                                user_id=user.id,
                                role_id="role-super-admin",
                                status="ACTIVE",
                            )
                        else:
                            user_mem.role_id = "role-super-admin"
    except Exception as err:
        logger.warning("Super Admin bootstrap warning: %s", err)


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
    await _bootstrap_super_admins()
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

