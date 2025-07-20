import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])
logger = logging.getLogger(__name__)


def timing_decorator(func: F) -> F:
    """
    A decorator that logs the execution time of a function.
    Works with both synchronous and asynchronous functions.
    """

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        start_time = time.monotonic()
        try:
            return await func(*args, **kwargs)
        finally:
            end_time = time.monotonic()
            total_time = end_time - start_time
            logger.info(
                f"Performance: {func.__name__} took {total_time:.4f} seconds to execute."
            )

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        start_time = time.monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            end_time = time.monotonic()
            total_time = end_time - start_time
            logger.info(
                f"Performance: {func.__name__} took {total_time:.4f} seconds to execute."
            )

    if asyncio.iscoroutinefunction(func):
        return async_wrapper  # type: ignore[return-value]
    else:
        return sync_wrapper  # type: ignore[return-value]
