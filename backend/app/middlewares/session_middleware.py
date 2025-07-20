from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings


def register_session(app: FastAPI) -> None:
    """Register session middleware with dedicated secret key."""
    settings = get_settings()
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,  # Use dedicated session secret
        max_age=settings.SESSION_COOKIE_MAX_AGE,
    )
