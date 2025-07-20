"""
Comprehensive error handling utilities for FastAPI applications.

This module provides decorators and helper functions to eliminate duplicate
error handling patterns and ensure consistent error responses across the application.
"""

import functools
import inspect
from typing import Any, Callable, Dict, NoReturn, Optional, ParamSpec, Type, TypeVar

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.services.llm.exceptions import LLMConfigurationError, LLMGenerationError

logger = get_logger(__name__)

T = TypeVar("T")
P = ParamSpec("P")


class ErrorMapping:
    """Centralized error mapping configuration."""

    # Database error mappings
    DATABASE_ERRORS: Dict[Type[Exception], tuple[int, str]] = {
        SQLAlchemyError: (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Database operation failed",
        ),
        IntegrityError: (
            status.HTTP_409_CONFLICT,
            "Data integrity constraint violation",
        ),
        DataError: (status.HTTP_400_BAD_REQUEST, "Invalid data format"),
    }

    # Network error mappings
    NETWORK_ERRORS: Dict[Type[Exception], tuple[int, str]] = {
        ConnectionError: (
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Service connection failed",
        ),
        TimeoutError: (status.HTTP_504_GATEWAY_TIMEOUT, "Service request timed out"),
        httpx.RequestError: (
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Network request failed",
        ),
        httpx.HTTPStatusError: (
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "External service error",
        ),
    }

    # Validation error mappings
    VALIDATION_ERRORS: Dict[Type[Exception], tuple[int, str]] = {
        ValueError: (status.HTTP_400_BAD_REQUEST, "Invalid input value"),
        ValidationError: (status.HTTP_422_UNPROCESSABLE_ENTITY, "Validation failed"),
        TypeError: (status.HTTP_400_BAD_REQUEST, "Invalid data type"),
        KeyError: (status.HTTP_400_BAD_REQUEST, "Missing required field"),
    }

    # LLM service error mappings
    LLM_ERRORS: Dict[Type[Exception], tuple[int, str]] = {
        LLMConfigurationError: (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "LLM service configuration error",
        ),
        LLMGenerationError: (
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "LLM generation failed",
        ),
    }

    # File operation error mappings
    FILE_ERRORS: Dict[Type[Exception], tuple[int, str]] = {
        FileNotFoundError: (status.HTTP_404_NOT_FOUND, "File not found"),
        PermissionError: (status.HTTP_403_FORBIDDEN, "Permission denied"),
        OSError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "File system error"),
    }


def get_error_mapping(error: Exception) -> tuple[int, str]:
    """
    Get appropriate HTTP status code and message for an exception.

    Args:
        error: The exception to map

    Returns:
        Tuple of (status_code, user_message)
    """
    error_type = type(error)

    # Check all error mappings
    for error_map in [
        ErrorMapping.DATABASE_ERRORS,
        ErrorMapping.NETWORK_ERRORS,
        ErrorMapping.VALIDATION_ERRORS,
        ErrorMapping.LLM_ERRORS,
        ErrorMapping.FILE_ERRORS,
    ]:
        for exception_type, (status_code, message) in error_map.items():
            if issubclass(error_type, exception_type):
                return status_code, message

    # Default to internal server error
    return status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error"


def log_error_with_context(
    error: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    log_level: str = "error",
) -> None:
    """
    Log an error with structured context information.

    Args:
        error: The exception to log
        operation: Description of the operation that failed
        context: Additional context information
        log_level: Log level (error, warning, info)
    """
    log_context = {
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
    }

    if context:
        log_context.update(context)

    log_message = f"{operation} failed: {error}"

    if log_level == "error":
        logger.error(log_message, extra=log_context, exc_info=True)
    elif log_level == "warning":
        logger.warning(log_message, extra=log_context)
    elif log_level == "info":
        logger.info(log_message, extra=log_context)


def create_http_exception(
    error: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    custom_message: Optional[str] = None,
) -> HTTPException:
    """
    Create an HTTPException from an error with consistent logging.

    Args:
        error: The original exception
        operation: Description of the operation that failed
        context: Additional context for logging
        custom_message: Custom user-facing message

    Returns:
        HTTPException with appropriate status code and message
    """
    # Log the error with context
    log_error_with_context(error, operation, context)

    # Get appropriate HTTP status and message
    status_code, default_message = get_error_mapping(error)

    # Use custom message if provided, otherwise use default
    user_message = custom_message or default_message

    return HTTPException(status_code=status_code, detail=user_message)


def handle_database_error(
    error: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    custom_message: Optional[str] = None,
) -> NoReturn:
    """
    Handle database errors with consistent logging and rollback.

    Args:
        error: The database error
        operation: Description of the operation that failed
        context: Additional context for logging
        custom_message: Custom user-facing message

    Raises:
        HTTPException: Appropriate HTTP error
    """
    raise create_http_exception(error, operation, context, custom_message)


def handle_network_error(
    error: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    custom_message: Optional[str] = None,
) -> NoReturn:
    """
    Handle network/external service errors.

    Args:
        error: The network error
        operation: Description of the operation that failed
        context: Additional context for logging
        custom_message: Custom user-facing message

    Raises:
        HTTPException: Appropriate HTTP error
    """
    raise create_http_exception(error, operation, context, custom_message)


def handle_validation_error(
    error: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    custom_message: Optional[str] = None,
) -> NoReturn:
    """
    Handle validation errors.

    Args:
        error: The validation error
        operation: Description of the operation that failed
        context: Additional context for logging
        custom_message: Custom user-facing message

    Raises:
        HTTPException: Appropriate HTTP error
    """
    raise create_http_exception(error, operation, context, custom_message)


def with_error_handling(
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    custom_messages: Optional[Dict[Type[Exception], str]] = None,
    rollback_session: bool = False,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for comprehensive error handling with automatic logging and HTTP exception conversion.

    Args:
        operation: Description of the operation being performed
        context: Additional context for logging
        custom_messages: Custom error messages for specific exception types
        rollback_session: Whether to rollback database session on error

    Returns:
        Decorator function
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                # The return type of func could be a coroutine, so we await it
                return await func(*args, **kwargs)  # type: ignore
            except HTTPException:
                # Re-raise HTTPExceptions without modification
                raise
            except Exception as e:
                # Handle database rollback if requested
                if rollback_session:
                    # Try to find AsyncSession in args/kwargs
                    db_session = None
                    for arg in args:
                        if isinstance(arg, AsyncSession):
                            db_session = arg
                            break
                    if db_session is None:
                        for value in kwargs.values():
                            if isinstance(value, AsyncSession):
                                db_session = value
                                break
                    if db_session:
                        try:
                            await db_session.rollback()
                        except Exception as rollback_error:
                            logger.error(
                                f"Failed to rollback session: {rollback_error}"
                            )

                # Get custom message if provided
                custom_message = None
                if custom_messages and type(e) in custom_messages:
                    custom_message = custom_messages[type(e)]

                # Create and raise appropriate HTTP exception
                raise create_http_exception(e, operation, context, custom_message)

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTPExceptions without modification
                raise
            except Exception as e:
                # Get custom message if provided
                custom_message = None
                if custom_messages and type(e) in custom_messages:
                    custom_message = custom_messages[type(e)]

                # Create and raise appropriate HTTP exception
                raise create_http_exception(e, operation, context, custom_message)

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper

    return decorator


def with_database_error_handling(
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    custom_message: Optional[str] = None,
    rollback: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator specifically for database operations with automatic rollback.

    Args:
        operation: Description of the database operation
        context: Additional context for logging
        custom_message: Custom user-facing message
        rollback: Whether to rollback session on error

    Returns:
        Decorator function
    """
    return with_error_handling(
        operation=operation,
        context=context,
        custom_messages={SQLAlchemyError: custom_message} if custom_message else None,
        rollback_session=rollback,
    )


def with_network_error_handling(
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    custom_message: Optional[str] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator specifically for network/external service operations.

    Args:
        operation: Description of the network operation
        context: Additional context for logging
        custom_message: Custom user-facing message

    Returns:
        Decorator function
    """
    network_messages = {}
    if custom_message:
        for error_type in [
            ConnectionError,
            TimeoutError,
            httpx.RequestError,
            httpx.HTTPStatusError,
        ]:
            network_messages[error_type] = custom_message

    return with_error_handling(
        operation=operation, context=context, custom_messages=network_messages
    )


def with_validation_error_handling(
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    custom_message: Optional[str] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator specifically for validation operations.

    Args:
        operation: Description of the validation operation
        context: Additional context for logging
        custom_message: Custom user-facing message

    Returns:
        Decorator function
    """
    validation_messages = {}
    if custom_message:
        for error_type in [ValueError, ValidationError, TypeError, KeyError]:
            validation_messages[error_type] = custom_message

    return with_error_handling(
        operation=operation, context=context, custom_messages=validation_messages
    )


# Convenience functions for common error scenarios
def raise_not_found_error(resource_name: str, detail: Optional[str] = None) -> NoReturn:
    """Raise a standardized 404 Not Found HTTPException."""
    if detail is None:
        detail = f"{resource_name} not found"
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_conflict_error(resource_name: str, detail: Optional[str] = None) -> NoReturn:
    """Raise a standardized 409 Conflict HTTPException."""
    if detail is None:
        detail = f"{resource_name} already exists"
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def raise_bad_request_error(detail: str) -> NoReturn:
    """Raise a standardized 400 Bad Request HTTPException."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def raise_unauthorized_error(detail: Optional[str] = None) -> NoReturn:
    """Raise a standardized 401 Unauthorized HTTPException."""
    if detail is None:
        detail = "Authentication required"
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def raise_forbidden_error(detail: Optional[str] = None) -> NoReturn:
    """Raise a standardized 403 Forbidden HTTPException."""
    if detail is None:
        detail = "Access forbidden"
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def raise_service_unavailable_error(detail: Optional[str] = None) -> NoReturn:
    """Raise a standardized 503 Service Unavailable HTTPException."""
    if detail is None:
        detail = "Service is currently unavailable"
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


def raise_internal_server_error(detail: Optional[str] = None) -> NoReturn:
    """Raise a standardized 500 Internal Server Error HTTPException."""
    if detail is None:
        detail = "Internal server error"
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
    )
