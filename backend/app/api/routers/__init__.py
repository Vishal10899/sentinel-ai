"""Versioned API router registrations."""

from app.api.routers.health import router as health_router
from app.api.routers.providers import router as catalog_router
from app.api.routers.routing import router as routing_router
from app.api.routers.cost import router as cost_router
from app.api.routers.auth import router as auth_router
from app.api.routers.workspace import router as workspace_router

__all__ = ["auth_router", "catalog_router", "cost_router", "health_router", "routing_router", "workspace_router"]
