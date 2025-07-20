"""
Task management API endpoints.

Provides endpoints for triggering and monitoring background tasks.
"""

from typing import Any, Dict

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.tasks import (
    DatabaseTaskRequest,
    ErrorTaskRequest,
    TaskResponse,
    TaskResultResponse,
    TaskStatus,
    TaskTriggerRequest,
)
from app.tasks.example_task import database_task, error_task, simple_task
from app.worker.celery_app import celery_app

router = APIRouter()


@router.post(
    "/simple",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Simple Task",
    description="Trigger a simple background task without database access.",
    tags=["Tasks"],
)
async def trigger_simple_task(
    request: TaskTriggerRequest,
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Trigger a simple background task."""
    task = simple_task.delay(request.message)

    return TaskResponse(
        task_id=task.id,
        status=TaskStatus.PENDING,
        message="Simple task queued successfully",
    )


@router.post(
    "/database",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Database Task",
    description="Trigger a background task with database access (example with safe operations only).",
    tags=["Tasks"],
)
async def trigger_database_task(
    request: DatabaseTaskRequest,
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Trigger a database background task with safe operations only."""
    # Security: Map operation names to allowed table names
    allowed_operations = {
        "count_users": "users",
        "count_api_keys": "api_keys",
        "get_user_stats": "users",
        "list_llm_settings": "llm_settings",
    }

    if request.query not in allowed_operations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation. Allowed operations: {list(allowed_operations.keys())}",
        )

    # Use the mapped table name
    table_name = allowed_operations[request.query]
    task = database_task.delay(table_name)

    return TaskResponse(
        task_id=task.id,
        status=TaskStatus.PENDING,
        message="Database task queued successfully",
    )


@router.post(
    "/error",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Error Task",
    description="Trigger a task that demonstrates error handling and retries.",
    tags=["Tasks"],
)
async def trigger_error_task(
    request: ErrorTaskRequest,
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Trigger an error task for testing purposes."""
    task = error_task.delay(request.should_fail)

    return TaskResponse(
        task_id=task.id,
        status=TaskStatus.PENDING,
        message="Error task queued successfully",
    )


@router.get(
    "/{task_id}",
    response_model=TaskResultResponse,
    summary="Get Task Result",
    description="Get the status and result of a background task.",
    tags=["Tasks"],
)
async def get_task_result(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
) -> TaskResultResponse:
    """Get task status and result."""
    try:
        result = AsyncResult(task_id, app=celery_app)

        task_status = TaskStatus(result.status)

        # Prepare response data
        result_data = None
        error_data = None
        completed_at = None

        if result.successful():
            result_data = result.result
        elif result.failed():
            error_data = str(result.info)

        # Add timing information if available
        if hasattr(result, "date_done") and result.date_done:
            completed_at = result.date_done.isoformat()

        return TaskResultResponse(
            task_id=task_id,
            status=task_status,
            result=result_data,
            error=error_data,
            created_at=None,  # Not available from AsyncResult
            completed_at=completed_at,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found or invalid: {str(e)}",
        )


@router.get(
    "/",
    summary="List Active Tasks",
    description="Get information about active tasks (requires Flower or custom implementation).",
    tags=["Tasks"],
)
async def list_active_tasks(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """List active tasks (placeholder - would require additional monitoring)."""
    return {
        "message": "Task listing not implemented",
        "suggestion": "Use Flower UI at http://localhost:5555 for task monitoring",
    }
