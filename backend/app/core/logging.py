"""Central logging configuration for the backend."""

import logging
from time import perf_counter

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


logger = logging.getLogger(__name__)


def configure_logging(log_level: str, log_format: str) -> None:
    """Configure the process-wide log format and severity threshold once."""
    logging.basicConfig(
        level=log_level.upper(),
        format=log_format,
        force=True,
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log one completion record for every API request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Log request method, path, otimezone.utcome, and duration without changing responses."""
        start_time = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - start_time) * 1_000
            logger.exception(
                "Request failed | method=%s path=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = (perf_counter() - start_time) * 1_000
        log_message = "Request completed | method=%s path=%s status_code=%s duration_ms=%.2f"
        log_arguments = (
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        if response.status_code >= 500:
            logger.error(log_message, *log_arguments)
        elif response.status_code >= 400:
            logger.warning(log_message, *log_arguments)
        else:
            logger.info(log_message, *log_arguments)

        return response
