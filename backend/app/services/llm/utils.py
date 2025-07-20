"""Shared utilities for LLM services."""

import asyncio
import functools
import json
import logging
from typing import Any, Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError

from .exceptions import LLMRateLimitError, LLMValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def parse_json_response(content: str, response_model: Type[T]) -> T:
    """
    Parse JSON response content into a Pydantic model.

    Args:
        content: Raw JSON string content
        response_model: Pydantic model class for validation

    Returns:
        Validated response instance

    Raises:
        LLMValidationError: If parsing or validation fails
    """
    try:
        # Try to parse as JSON first
        if content.strip().startswith("{") or content.strip().startswith("["):
            return response_model.model_validate_json(content)
        else:
            # If not JSON, try to extract JSON from the content
            # This handles cases where the LLM returns text with JSON embedded
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_content = content[start_idx:end_idx]
                return response_model.model_validate_json(json_content)
            else:
                raise LLMValidationError(
                    f"No valid JSON found in response: {content[:100]}..."
                )
    except (json.JSONDecodeError, ValidationError) as e:
        raise LLMValidationError(
            f"Failed to parse response into {response_model.__name__}: {e}"
        ) from e


def _is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an exception represents a transient error that should be retried.

    Args:
        exception: The exception to check

    Returns:
        True if the error is transient and should be retried, False otherwise
    """
    # Import here to avoid circular imports
    try:
        from botocore.exceptions import BotoCoreError, ClientError
        from openai import APIError
        from openai import RateLimitError as OpenAIRateLimitError
    except ImportError:
        # If imports fail, be conservative and don't retry
        return False

    # Always retry on our custom rate limit error
    if isinstance(exception, LLMRateLimitError):
        return True

    # OpenAI specific errors
    if isinstance(exception, OpenAIRateLimitError):
        return True

    if isinstance(exception, APIError):
        # Retry on server errors (5xx) and rate limits, but not client errors (4xx)
        # Try to get status code from various possible locations
        status_code = getattr(exception, "status_code", None)
        if status_code is None:
            # Try to get from response attribute if it exists
            response = getattr(exception, "response", None)
            if response is not None:
                status_code = getattr(response, "status_code", None)

        if status_code is not None:
            # Retry on server errors (500-599) and rate limit (429)
            if status_code >= 500 or status_code == 429:
                return True

        # Also check for timeout-related errors in the message
        error_msg = str(exception).lower()
        if any(
            keyword in error_msg for keyword in ["timeout", "timed out", "connection"]
        ):
            return True
        return False

    # Bedrock/AWS specific errors
    if isinstance(exception, ClientError):
        error_code = exception.response.get("Error", {}).get("Code", "")
        # Retry on throttling and server errors, but not on client errors
        retryable_codes = {
            "ThrottlingException",
            "ServiceUnavailableException",
            "InternalServerException",
            "TooManyRequestsException",
            "RequestTimeoutException",
        }
        if error_code in retryable_codes:
            return True
        return False

    if isinstance(exception, BotoCoreError):
        # Retry on connection and timeout errors
        error_msg = str(exception).lower()
        if any(
            keyword in error_msg for keyword in ["timeout", "connection", "network"]
        ):
            return True
        return False

    # Standard Python exceptions that might be transient
    if isinstance(exception, (asyncio.TimeoutError, TimeoutError)):
        return True

    if isinstance(exception, (ConnectionError, OSError)):
        return True

    # Don't retry on other exceptions (validation errors, access denied, etc.)
    return False


def retry_on_failure(
    max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0
) -> Callable[[Callable], Callable]:
    """
    Decorator to retry async functions on transient failures with exponential backoff.

    Only retries on transient errors like timeouts, rate limits, and temporary network issues.
    Does not retry on permanent errors like validation errors, access denied, etc.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            last_exception: Exception | None = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if this is a retryable error
                    if not _is_retryable_error(e):
                        # Log with more context for specific error types
                        if isinstance(e, (ValidationError, ValueError)):
                            logger.info(
                                f"Validation error in {func.__name__}: {e}. "
                                f"Not retrying."
                            )
                        elif isinstance(e, PermissionError):
                            logger.info(
                                f"Permission error in {func.__name__}: {e}. "
                                f"Not retrying."
                            )
                        else:
                            logger.info(
                                f"Non-retryable error in {func.__name__}: {e}. "
                                f"Not retrying."
                            )
                        raise e

                    if attempt < max_retries:
                        logger.warning(
                            f"Retryable error in {func.__name__} (attempt {attempt + 1}): {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__} "
                            f"with retryable error: {e}"
                        )

            # This should never happen since we always catch exceptions above
            if last_exception is not None:
                raise last_exception
            else:
                raise RuntimeError(
                    f"Unexpected error in retry logic for {func.__name__}"
                )

        return wrapper

    return decorator
