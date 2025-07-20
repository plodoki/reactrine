"""
API utilities for common HTTP operations and error handling.

This module provides reusable functions for common API operations
and standardized error handling patterns.
"""

from typing import Awaitable, Callable, NoReturn, ParamSpec, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.services.llm.exceptions import LLMConfigurationError, LLMGenerationError
from app.utils.error_handling import (
    create_http_exception,
    handle_database_error,
    raise_internal_server_error,
    raise_service_unavailable_error,
    with_error_handling,
)

logger = get_logger(__name__)

T = TypeVar("T")
P = ParamSpec("P")


# Legacy functions for backward compatibility - now use centralized error handling
async def handle_database_error_legacy(
    db: AsyncSession, operation: str, error: SQLAlchemyError, rollback: bool = True
) -> NoReturn:
    """
    Handle database errors with consistent logging and rollback.

    Args:
        db: Database session
        operation: Description of the operation that failed
        error: The SQLAlchemy error that occurred
        rollback: Whether to rollback the session

    Raises:
        HTTPException: 500 Internal Server Error
    """
    if rollback:
        await db.rollback()

    handle_database_error(error, operation)


def handle_llm_error(error: Exception, operation: str) -> NoReturn:
    """
    Handle LLM service errors with appropriate HTTP status codes.

    Args:
        error: The LLM error that occurred
        operation: Description of the operation that failed

    Raises:
        HTTPException: Appropriate HTTP error based on error type
    """
    if isinstance(error, LLMConfigurationError):
        raise_internal_server_error("LLM service is not configured properly")
    elif isinstance(error, LLMGenerationError):
        raise_service_unavailable_error(
            "The AI service is currently unavailable or failed to complete the request"
        )
    else:
        raise create_http_exception(error, operation)


async def with_database_error_handling(
    db: AsyncSession,
    operation: str,
    func: Callable[P, Awaitable[T]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """
    Execute a database operation with automatic error handling.

    Args:
        db: Database session
        operation: Description of the operation
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Result of the function execution

    Raises:
        HTTPException: If a database error occurs
    """
    try:
        return await func(*args, **kwargs)
    except SQLAlchemyError as e:
        await handle_database_error_legacy(db, operation, e)


def with_llm_error_handling(
    operation: str,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for handling LLM service errors.

    Args:
        operation: Description of the operation

    Returns:
        Decorator function
    """
    return with_error_handling(
        operation=operation,
        custom_messages={
            LLMConfigurationError: "LLM service is not configured properly",
            LLMGenerationError: "The AI service is currently unavailable or failed to complete the request",
        },
    )
