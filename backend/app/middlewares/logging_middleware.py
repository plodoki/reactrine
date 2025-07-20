from fastapi import FastAPI

from app.core.logging import LoggingMiddleware


def register_logging(app: FastAPI) -> None:
    """Register logging middleware."""
    app.add_middleware(LoggingMiddleware)
