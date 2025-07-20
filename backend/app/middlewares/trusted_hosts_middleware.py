from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings


def register_trusted_hosts(app: FastAPI) -> None:
    """Register TrustedHost middleware using configured hosts."""
    settings = get_settings()
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)
