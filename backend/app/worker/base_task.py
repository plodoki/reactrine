"""
Base task classes for Celery workers.

Provides database session management and logging for background tasks.
"""

import asyncio
from typing import Any, Callable, Optional

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.worker.celery_app import celery_app

logger = get_logger(__name__)


class DatabaseTask(Task):
    """
    Base task class that provides database session management.

    Automatically handles async database operations in sync Celery context.
    """

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the task with proper async handling."""
        if asyncio.iscoroutinefunction(self.run):
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    # If we're in a running loop, execute in a separate thread
                    import concurrent.futures

                    def run_in_thread() -> Any:
                        return asyncio.run(self.run(*args, **kwargs))

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_thread)
                        return future.result()
                else:
                    return loop.run_until_complete(self.run(*args, **kwargs))
            except RuntimeError:
                # No event loop running, create a new one
                return asyncio.run(self.run(*args, **kwargs))
        return self.run(*args, **kwargs)

    async def run_with_db(self, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        """Override this method to implement task logic with database access."""
        raise NotImplementedError("Subclasses must implement run_with_db")

    async def run(self, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        """Execute task with database session."""
        async with async_session_factory() as session:
            try:
                result = await self.run_with_db(session, *args, **kwargs)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logger.error(f"Task {self.name} failed: {e}")
                raise
            finally:
                await session.close()


def task_with_db(
    name: Optional[str] = None,
    **celery_kwargs: Any,  # noqa: ANN401
) -> Callable[[Callable[..., Any]], Any]:  # noqa: ANN401
    """
    Decorator to create database-aware Celery tasks.

    Usage:
        @task_with_db(name="my_task")
        async def my_task(db: AsyncSession, arg1: str) -> str:
            # Task implementation with database access
            return "result"
    """

    def decorator(func: Callable[..., Any]) -> Any:  # noqa: ANN401
        task_name = name or f"{func.__module__}.{func.__name__}"

        class DatabaseTaskWrapper(DatabaseTask):
            name = task_name  # Set the name for Celery registration

            async def run_with_db(
                self,
                session: AsyncSession,
                *args: Any,  # noqa: ANN401
                **kwargs: Any,  # noqa: ANN401
            ) -> Any:  # noqa: ANN401
                return await func(session, *args, **kwargs)

        task_obj = celery_app.register_task(DatabaseTaskWrapper())
        return task_obj

    return decorator
