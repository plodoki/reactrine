import secrets
import time
import uuid
from collections.abc import Awaitable
from typing import Callable

import structlog
from fastapi import FastAPI, Request, Response
from starlette.datastructures import MutableHeaders

# HTTP Header constants
HEADER_REQUEST_ID = "X-Request-ID"
HEADER_PROCESS_TIME = "X-Process-Time"
HEADER_CONTENT_TYPE_OPTIONS = "X-Content-Type-Options"
HEADER_FRAME_OPTIONS = "X-Frame-Options"
HEADER_CSP = "Content-Security-Policy"
HEADER_HSTS = "Strict-Transport-Security"
HEADER_REFERRER_POLICY = "Referrer-Policy"
HEADER_PERMISSIONS_POLICY = "Permissions-Policy"
HEADER_XSS_PROTECTION = "X-XSS-Protection"

logger = structlog.get_logger(__name__)


def register_request_id_and_timing(app: FastAPI) -> None:
    """Register HTTP middleware to add request ID, timing, and security headers."""

    @app.middleware("http")
    async def add_request_id_and_timing(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(HEADER_REQUEST_ID, str(uuid.uuid4()))
        request.state.request_id = request_id

        # Generate a CSP nonce for inline scripts/styles
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        start_time = time.time()
        try:
            response: Response = await call_next(request)
        except Exception:
            logger.exception(
                "Error during request processing",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
            )
            raise

        process_time = time.time() - start_time

        # Set response headers
        headers: MutableHeaders = response.headers
        headers[HEADER_REQUEST_ID] = request_id
        headers[HEADER_PROCESS_TIME] = str(process_time)

        # Security headers
        headers[HEADER_CONTENT_TYPE_OPTIONS] = "nosniff"
        headers[HEADER_FRAME_OPTIONS] = "DENY"

        # Content Security Policy - more permissive for API docs
        if request.url.path.endswith(("/docs", "/redoc")):
            csp_value = (
                "default-src 'self' https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' https://fastapi.tiangolo.com data:; "
                "font-src 'self' https://cdn.jsdelivr.net"
            )
        else:
            csp_value = (
                f"default-src 'self' https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
                f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
                f"style-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
                f"img-src 'self' https://fastapi.tiangolo.com data:; "
                f"font-src 'self' https://cdn.jsdelivr.net"
            )
        headers[HEADER_CSP] = csp_value

        # Additional security headers
        headers[HEADER_HSTS] = "max-age=63072000; includeSubDomains; preload"
        headers[HEADER_REFERRER_POLICY] = "no-referrer"
        headers[HEADER_PERMISSIONS_POLICY] = "geolocation=(), camera=(), microphone=()"
        headers[HEADER_XSS_PROTECTION] = "1; mode=block"

        return response
