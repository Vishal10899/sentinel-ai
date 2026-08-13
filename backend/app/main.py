import os
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Connection._cancel.*")

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.orchestration.exceptions import SentinelEnterpriseError
from app.api.routers import (
    auth_router,
    chat_router,
    cost_router,
    health_router,
    providers_router,
    routing_router,
    workspace_router,
)
from app.core.lifecycle import lifespan
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.core.settings import settings
from app.api.routers.conversation import router as conversation_router
from app.api.routers.files import router as files_router
from app.api.routers.policies import router as policies_router
from app.api.routers.cache import router as cache_router
from app.api.routers.guardrails import router as guardrails_router
from app.api.routers.virtual_keys import router as virtual_keys_router
from app.api.routers.roles import router as roles_router
from app.api.routers.audit import router as audit_router
from app.api.routers.finops import router as finops_router
from app.api.routers.observability import router as observability_router
from app.api.routers.tenancy import router as tenancy_router
from app.api.routers.messages import router as messages_router
from app.api.routers.reliability import router as reliability_router
from app.api.routers.security import router as security_router
from app.api.routers.system import router as system_router
from app.api.routers.openai_gateway import router as openai_gateway_router
from app.api.routers.mcp import router as mcp_router
from app.api.routers.users import router as users_router


# Configure logging once before application startup.
configure_logging(settings.log_level, settings.log_format)

logger = logging.getLogger(__name__)

# Application composition only: transport concerns and routers are kept modular.
app = FastAPI(
    title=settings.project_title,
    version=settings.project_version,
    description=settings.project_description,
    lifespan=lifespan,
)


@app.exception_handler(SentinelEnterpriseError)
async def sentinel_enterprise_exception_handler(request: Request, exc: SentinelEnterpriseError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "details": exc.details},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception | method=%s path=%s: %s",
        request.method,
        request.url.path,
        str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


# Browser clients are limited to the configured, explicit origins or ALLOWED_ORIGINS env var.
raw_allowed_origins = os.environ.get("ALLOWED_ORIGINS") or os.environ.get("SENTINEL_AI_ALLOWED_ORIGINS")
if raw_allowed_origins:
    allowed_origins = [o.strip() for o in raw_allowed_origins.split(",") if o.strip()]
else:
    allowed_origins = settings.cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https?://.*",
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Log each request independently of endpoint implementation details.
app.add_middleware(RequestLoggingMiddleware)

from fastapi.responses import PlainTextResponse
from app.core.metrics import metrics_exporter


@app.get("/metrics", response_class=PlainTextResponse, tags=["metrics"], summary="Prometheus exposition metrics")
async def prometheus_metrics():
    """Expose real-time control plane telemetry in Prometheus format."""
    return metrics_exporter.generate_metrics_payload()


app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(system_router, prefix=settings.api_v1_prefix)
app.include_router(reliability_router, prefix=settings.api_v1_prefix)
app.include_router(security_router, prefix=settings.api_v1_prefix)
app.include_router(providers_router, prefix=settings.api_v1_prefix)
app.include_router(routing_router, prefix=settings.api_v1_prefix)
app.include_router(cost_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(workspace_router, prefix=settings.api_v1_prefix)
app.include_router(chat_router, prefix=settings.api_v1_prefix)
app.include_router(conversation_router, prefix=settings.api_v1_prefix)
app.include_router(messages_router, prefix=settings.api_v1_prefix)
app.include_router(files_router, prefix=settings.api_v1_prefix)
app.include_router(policies_router, prefix=settings.api_v1_prefix)
app.include_router(cache_router, prefix=settings.api_v1_prefix)
app.include_router(guardrails_router, prefix=settings.api_v1_prefix)
app.include_router(virtual_keys_router, prefix=settings.api_v1_prefix)
app.include_router(roles_router, prefix=settings.api_v1_prefix)
app.include_router(audit_router, prefix=settings.api_v1_prefix)
app.include_router(finops_router, prefix=settings.api_v1_prefix)
app.include_router(observability_router, prefix=settings.api_v1_prefix)
app.include_router(tenancy_router, prefix=settings.api_v1_prefix)
app.include_router(mcp_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(openai_gateway_router)


