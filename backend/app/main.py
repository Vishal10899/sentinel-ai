from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth_router, catalog_router, cost_router, health_router, routing_router, workspace_router
from app.core.lifecycle import lifespan
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.core.settings import settings


# Configure logging once before application startup.
configure_logging(settings.log_level, settings.log_format)

# Application composition only: transport concerns and routers are kept modular.
app = FastAPI(
    title=settings.project_title,
    version=settings.project_version,
    description=settings.project_description,
    lifespan=lifespan,
)

# Browser clients are limited to the configured, explicit origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Log each request independently of endpoint implementation details.
app.add_middleware(RequestLoggingMiddleware)

# All public API endpoints are versioned from their first release.
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(catalog_router, prefix=settings.api_v1_prefix)
app.include_router(routing_router, prefix=settings.api_v1_prefix)
app.include_router(cost_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(workspace_router, prefix=settings.api_v1_prefix)
