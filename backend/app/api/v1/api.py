from typing import Any, Dict

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.endpoints import admin, api_keys, auth, haiku, jwks, llm_settings, tasks
from app.core.config import settings
from app.core.logging import log_exception
from app.db.session import check_database_connection

# Create main API router
api_router = APIRouter()


# Health check endpoint
@api_router.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """Check service health including database connectivity."""
    db_status = await check_database_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "details": {
            "database": "connected" if db_status else "disconnected",
            "api": "running",
        },
        "version": settings.ENVIRONMENT,
    }


# Include additional resource routers here
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    api_keys.router, prefix="/users/me/api-keys", tags=["api-keys"]
)
api_router.include_router(haiku.router)
api_router.include_router(jwks.router, tags=["jwks"])
api_router.include_router(llm_settings.router)
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(items.router, prefix="/items", tags=["items"])


# Exception handlers to register with the application
def add_exception_handlers(app: FastAPI) -> None:
    """Add global exception handlers to the FastAPI application."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle validation errors with structured response."""
        # Log the error
        log_exception(exc, request)

        # Extract error details
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "loc": error.get("loc", []),
                    "msg": error.get("msg", "Validation error"),
                    "type": error.get("type", "value_error"),
                }
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": errors,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions with logging."""
        # Don't log expected authentication/authorization errors as exceptions
        # These are normal business logic responses, not system errors
        if exc.status_code not in (401, 403):
            # Log the error for non-auth exceptions
            log_exception(exc, request)

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError with structured response."""
        # Log the error
        log_exception(exc, request)

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions with logging."""
        # Log the error
        log_exception(exc, request)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )


# Function to initialize the API with versioning
def initialize_api(app: FastAPI) -> None:
    """Initialize the API with version prefix and exception handlers."""
    # Add API router with version prefix
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Add exception handlers
    add_exception_handlers(app)

    # Add middleware for request timing and performance monitoring
    # App-specific middleware would be registered here
