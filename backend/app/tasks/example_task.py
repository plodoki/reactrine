"""
Example background tasks demonstrating various patterns.

Includes simple tasks, database-aware tasks, and error handling examples.
"""

import datetime
from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.worker.base_task import task_with_db
from app.worker.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task
def simple_task(message: str) -> Dict[str, Any]:
    """
    Simple task without database access.

    Args:
        message: Input message to process

    Returns:
        Dictionary with task result
    """
    import time

    logger.info(f"Processing simple task with message: {message}")

    # Simulate some work (keeping time.sleep for compatibility with Celery)
    time.sleep(2)

    result = {
        "message": message,
        "processed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "completed",
    }

    logger.info(f"Simple task completed: {result}")
    return result


@task_with_db()
async def database_task(db: AsyncSession, table_name: str = "users") -> Dict[str, Any]:
    """
    Example task with database access.

    Args:
        db: Database session (injected by decorator)
        table_name: Table name to query (validated against whitelist)

    Returns:
        Dictionary with query results
    """
    logger.info(f"Executing database task for table: {table_name}")

    # Whitelist allowed table names to prevent SQL injection
    allowed_tables = {"users", "api_keys", "llm_settings", "refresh_tokens"}

    if table_name not in allowed_tables:
        raise ValueError(
            f"Table '{table_name}' not allowed. Allowed tables: {allowed_tables}"
        )

    try:
        # Use validated table name in query (safe after whitelist validation)
        query = text(f"SELECT * FROM {table_name} LIMIT 10")
        result = await db.execute(query)
        rows = result.fetchall()

        response = {
            "table_name": table_name,
            "row_count": len(rows),
            "results": [dict(row._mapping) for row in rows],
            "status": "completed",
        }

        logger.info(f"Database task completed: {response}")
        return response

    except Exception as e:
        logger.error(f"Database task failed: {e}")
        raise


@celery_app.task(bind=True, max_retries=3, countdown=60)
def error_task(self: Any, should_fail: bool = True) -> Dict[str, Any]:  # noqa: ANN401
    """
    Example task demonstrating error handling and retries.

    Args:
        should_fail: Whether the task should fail

    Returns:
        Dictionary with task result

    Raises:
        Exception: If should_fail is True
    """
    logger.info(f"Running error task (attempt {self.request.retries + 1})")

    if should_fail and self.request.retries < 2:
        logger.warning("Task intentionally failing for retry demonstration")
        try:
            raise Exception("Intentional failure for testing")
        except Exception as exc:
            raise self.retry(exc=exc)

    result = {
        "attempts": self.request.retries + 1,
        "status": "completed",
        "message": "Task succeeded after retries",
    }

    logger.info(f"Error task completed: {result}")
    return result
