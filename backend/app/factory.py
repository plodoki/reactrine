from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.v1.api import initialize_api
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.init_db import init_database
from app.db.session import async_session_factory, close_db_connection
from app.middlewares.cors_middleware import register_cors
from app.middlewares.logging_middleware import register_logging
from app.middlewares.rate_limit import register_rate_limit
from app.middlewares.request_timing_middleware import register_request_id_and_timing
from app.middlewares.session_middleware import register_session
from app.middlewares.trusted_hosts_middleware import register_trusted_hosts


def create_app() -> FastAPI:
    """Application factory for creating FastAPI app instances."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        setup_logging()
        # Database migrations are now handled manually or as part of deployment process
        # Removed automatic migration on startup to avoid issues

        # Skip database initialization in test environment
        if settings.ENVIRONMENT != "test":
            # Initialize database with default data
            async with async_session_factory() as db:
                await init_database(db)

        yield

        # Skip database connection cleanup in test environment
        if settings.ENVIRONMENT != "test":
            await close_db_connection()

    app = FastAPI(
        lifespan=lifespan,
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        openapi_url=settings.OPENAPI_URL,
    )

    # Register middlewares
    register_rate_limit(app)
    register_cors(app)
    register_trusted_hosts(app)
    register_session(app)
    register_logging(app)
    register_request_id_and_timing(app)

    # Initialize API routes with versioning
    initialize_api(app)

    return app
