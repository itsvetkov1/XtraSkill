"""
LoggingMiddleware for HTTP request/response logging with correlation ID propagation.

Key features:
- Generates or extracts correlation ID from X-Correlation-ID header
- Stores correlation ID in contextvars for async-safe request-scoped access
- Logs request start and completion with timing
- Adds X-Correlation-ID to response headers for frontend correlation
- Varies log level based on response status (INFO for success, WARNING for errors)
"""
import time
import uuid
from contextvars import ContextVar
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.services.logging_service import get_logging_service

# Context variable for correlation ID (async-safe, request-scoped)
_correlation_id_ctx: ContextVar[Optional[str]] = ContextVar(
    'correlation_id',
    default=None
)


def get_correlation_id() -> Optional[str]:
    """
    Get the correlation ID for the current request.

    Returns:
        Optional[str]: Correlation ID if set, None otherwise

    Example:
        from app.middleware.logging_middleware import get_correlation_id

        correlation_id = get_correlation_id()
        logging_service.log('INFO', 'Processing', 'api', correlation_id=correlation_id)
    """
    return _correlation_id_ctx.get()


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID for the current request.

    Args:
        correlation_id: Correlation ID to set

    This is called automatically by LoggingMiddleware, but can be used
    to override if needed.
    """
    _correlation_id_ctx.set(correlation_id)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware for HTTP request/response logging with correlation ID propagation.

    Architecture:
    - Extracts X-Correlation-ID from request header (or generates if missing)
    - Stores in contextvars for async-safe access throughout request lifecycle
    - Logs request start (method, path, correlation ID, user ID if available)
    - Logs response completion (status, duration)
    - Adds X-Correlation-ID to response headers

    This enables:
    - Request tracing across distributed systems
    - Frontend/backend log correlation
    - Performance monitoring (request duration)
    - Error investigation (correlation ID in both logs and headers)
    """

    def __init__(self, app: ASGIApp):
        """Initialize middleware with FastAPI app."""
        super().__init__(app)
        self.logging_service = get_logging_service()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process HTTP request with correlation ID and logging.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response: HTTP response with X-Correlation-ID header
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get('X-Correlation-ID')
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Store in context variable for access during request processing
        set_correlation_id(correlation_id)

        # Extract user ID if available (from JWT or session)
        user_id = None
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id

        # Start timing
        start_time = time.perf_counter()

        # Log request start
        self.logging_service.log(
            'INFO',
            f'{request.method} {request.url.path}',
            'api',
            correlation_id=correlation_id,
            method=request.method,
            path=str(request.url.path),
            query_params=dict(request.query_params),
            user_id=user_id,
            http_event='request_start'
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = 'ERROR'
        elif response.status_code >= 400:
            log_level = 'WARNING'
        else:
            log_level = 'INFO'

        # Log response
        self.logging_service.log(
            log_level,
            f'{request.method} {request.url.path} {response.status_code}',
            'api',
            correlation_id=correlation_id,
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            user_id=user_id,
            http_event='request_complete'
        )

        # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = correlation_id

        return response
