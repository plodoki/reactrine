import logging
import logging.handlers
import os
import sys
import uuid
from time import monotonic
from typing import Any, Dict, List, Optional

import structlog
from fastapi import HTTPException, Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings


def _extract_request_context(request: Request) -> Dict[str, Any]:
    """Extract base context fields from a request."""
    return {
        "request_id": get_request_id(request),
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else None,
    }


def setup_logging() -> None:
    """Configure simplified logging for the application."""
    # Clear any existing handlers
    logging.root.handlers.clear()

    # Also clear handlers for specific loggers that might have been configured
    for logger_name in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy.engine",
    ]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True

    # Set logging level based on settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    logging.root.setLevel(log_level)

    # Configure structlog processors based on environment
    processors: List[Any] = []

    if settings.ENVIRONMENT == "production":
        # Production: JSON output for structured logging
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]

        # Console handler with JSON format
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)
        logging.root.addHandler(console_handler)

        # File handler with rotation for production
        os.makedirs("logs", exist_ok=True, mode=0o755)
        file_handler = logging.handlers.RotatingFileHandler(
            "logs/app.log",
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        logging.root.addHandler(file_handler)

        # Configure structlog for production
        structlog.configure(
            processors=processors,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    else:
        # Development: Use simple standard logging, no structlog complexity
        # Console handler with colored output for development
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)

        # Simple, clean formatter for development - single timestamp and level
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)
        logging.root.addHandler(console_handler)

        # Configure specific loggers to reduce noise in development
        # Completely disable SQLAlchemy logging in development
        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
        sqlalchemy_logger.setLevel(logging.WARNING)
        sqlalchemy_logger.handlers.clear()
        sqlalchemy_logger.propagate = False  # Prevent propagation to root

        # Configure uvicorn loggers to use our format
        for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
            logger = logging.getLogger(logger_name)
            logger.setLevel(log_level)

        # Configure structlog to use standard logging in development
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.UnicodeDecoder(),
                structlog.processors.KeyValueRenderer(key_order=["event"]),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    # Log startup message with standard logging to avoid duplicate timestamps
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized - level={settings.LOG_LEVEL}, environment={settings.ENVIRONMENT}, handlers={len(logging.root.handlers)}"
    )


def get_logger(name: str) -> Any:  # noqa: ANN401
    """Get a logger instance for the specified name."""
    return structlog.get_logger(name)


def get_request_id(request: Request) -> str:
    """Extract request ID from request headers or generate a new one."""
    if hasattr(request.state, "request_id"):
        request_id: str = request.state.request_id
        return request_id

    # Respect inbound X-Request-ID header for trace propagation
    header_id = request.headers.get("X-Request-ID")
    if header_id:
        request.state.request_id = header_id
        return header_id

    new_id = str(uuid.uuid4())
    request.state.request_id = new_id
    return new_id


class LoggingMiddleware:
    """Middleware to log request and response details."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.logger = structlog.get_logger(__name__)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # Pass through non-HTTP requests (WebSocket, lifespan)
            await self.app(scope, receive, send)
            return

        # Create a request object
        request = Request(scope, receive)

        # Capture start time
        start_time = monotonic()

        # Get or create request ID
        request_id = get_request_id(request)

        # Set request ID in state
        request.state.request_id = request_id

        # Create context for this request
        log_ctx = make_log_context(request)

        # Log request start
        self.logger.info("Request started", **log_ctx)

        # Create a response interceptor for logging
        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_ctx = make_log_context(request, start_time=start_time)
                self.logger.info(
                    "Request completed",
                    status_code=message.get("status", 0),
                    **response_ctx,
                )

                message.setdefault("headers", []).append(
                    (b"X-Request-ID", request_id.encode())
                )

            await send(message)

        # Process the request
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Don't log expected authentication/authorization errors as failed requests
            if isinstance(e, HTTPException) and e.status_code in (401, 403):
                # These are expected for unauthenticated/unauthorized access
                # The exception will still be properly handled by FastAPI's exception handlers
                # We still log the request completion but not as an error
                response_ctx = make_log_context(request, start_time=start_time)
                self.logger.info(
                    "Request completed",
                    status_code=e.status_code,
                    **response_ctx,
                )
                raise

            # Log other exceptions as request failures
            self.logger.exception("Request failed", error=str(e), **log_ctx)
            raise


# Helper function to log exceptions
def log_exception(exc: Exception, request: Optional[Request] = None) -> None:
    """Log an exception with context from the request if available."""
    logger = structlog.get_logger(__name__)
    log_ctx = {}

    if request:
        log_ctx = {
            "request_id": get_request_id(request),
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        }

    logger.exception("Unhandled exception", error=str(exc), **log_ctx)


def make_log_context(
    request: Request, start_time: Optional[float] = None
) -> Dict[str, Any]:
    """Create logging context from request."""
    ctx = _extract_request_context(request)
    ctx["user_agent"] = request.headers.get("user-agent")
    if start_time is not None:
        ctx["duration_ms"] = round((monotonic() - start_time) * 1000, 2)
    return ctx


# Attach request context to logs
def attach_request_context(request: Request) -> Dict[str, Any]:
    """Extract context from a request for logging."""
    return _extract_request_context(request)
