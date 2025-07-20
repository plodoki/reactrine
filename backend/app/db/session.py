import asyncio
import functools
from collections.abc import AsyncGenerator, Awaitable
from typing import Callable, Optional, ParamSpec, Tuple, Type, TypeVar

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.logging import get_logger

"""
session.py
---------
Provides async database session management for FastAPI endpoints, including
engine creation, session dependency, transaction retry decorator, and health checks.

Functions:
    create_db_and_tables: Initialize database schema at startup.
    close_db_connection: Dispose of the database engine on shutdown.
    get_db_session: Yield an async session for endpoint dependencies.
    with_transaction_retry: Decorator to retry transient DB errors with backoff.
    check_database_connection: Verify connectivity by executing a simple query.
"""

logger = get_logger(__name__)

# Create async engine with connection pooling and automatic health checks
# Use the async-specific database URL from settings
url = make_url(settings.ASYNC_DATABASE_URL)
engine = create_async_engine(
    url,
    # Enable echo in development when debugging is enabled
    echo=settings.ENVIRONMENT == "development" and settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_db_and_tables() -> None:
    """
    Create database tables on application startup.

    This function is intended to be called once when the application starts.

    Raises:
        Exception: If table creation fails.
    """
    try:
        async with engine.begin() as conn:
            # Create tables from all SQLModel models
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables created successfully")
    except ConnectionError as e:
        logger.error(f"Database connection error creating tables: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


async def close_db_connection() -> None:
    """
    Close database connection on application shutdown.

    Disposes of the engine and releases all pooled connections.

    Raises:
        Exception: If disposing the engine fails.
    """
    try:
        await engine.dispose()
        logger.info("Database connection closed")
    except ConnectionError as e:
        logger.error(f"Database connection error during shutdown: {str(e)}")
    except Exception as e:
        logger.error(f"Error closing database connection: {str(e)}")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional async database session for FastAPI dependencies.
    Commits only if there are pending mutations.
    """
    session = async_session_factory()
    try:
        yield session
        # Commit only if session has changes
        if session.new or session.dirty or session.deleted:
            await session.commit()
    except Exception as e:
        await session.rollback()

        # Don't log authentication/authorization errors as database errors
        # These are expected when users access protected endpoints without auth
        from fastapi import HTTPException

        if isinstance(e, HTTPException) and e.status_code in (401, 403):
            # Re-raise without logging as a database error
            raise

        # Log actual database errors with specific handling
        from sqlalchemy.exc import SQLAlchemyError

        if isinstance(e, SQLAlchemyError):
            logger.error(f"Database error, rolling back: {e}")
        else:
            logger.error(f"Database session error, rolling back: {e}")
        raise
    finally:
        await session.close()


# Database transaction retry decorator
T = TypeVar("T")
P = ParamSpec("P")


def with_transaction_retry(
    max_retries: int = 3, retry_on: Optional[Tuple[Type[Exception], ...]] = None
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Decorator factory to retry async database operations on transient errors.

    Args:
        max_retries (int): Maximum retry attempts. Defaults to 3.
        retry_on (Optional[Tuple[Type[Exception], ...]]): Exceptions that trigger a retry.
            Defaults to (OperationalError, DBAPIError).

    Returns:
        Callable: A decorator that wraps an async function with retry logic.
    """
    if retry_on is None:
        # Default to retrying on common transient database errors
        from sqlalchemy.exc import DBAPIError, OperationalError

        retry_on = (OperationalError, DBAPIError)

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_error = e
                    logger.warning(
                        f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    # Exponential backoff
                    await asyncio.sleep(2**attempt)

            logger.error(f"Database operation failed after {max_retries} attempts")
            assert last_error is not None
            raise last_error

        return wrapper

    return decorator


# Health check function
@with_transaction_retry(max_retries=2)
async def check_database_connection() -> bool:
    """
    Check if the database connection is healthy by executing a simple query.

    Returns:
        bool: True if the query succeeds, False otherwise.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except ConnectionError as e:
        logger.error(f"Database connection check failed - connection error: {str(e)}")
        return False
    except TimeoutError as e:
        logger.error(f"Database connection check failed - timeout: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False
