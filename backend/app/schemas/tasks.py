"""
Task-related Pydantic schemas for request/response validation.
"""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class TaskTriggerRequest(BaseModel):
    """Request schema for triggering a simple task."""

    message: str = Field(..., description="Message to process")


class DatabaseTaskRequest(BaseModel):
    """Request schema for triggering a database task."""

    query: str = Field(
        ...,
        description="Database operation to execute (allowed: count_users, count_api_keys, get_user_stats, list_llm_settings)",
        min_length=1,
    )


class ErrorTaskRequest(BaseModel):
    """Request schema for triggering an error task."""

    should_fail: bool = Field(default=True, description="Whether the task should fail")


class TaskResponse(BaseModel):
    """Response schema for task operations."""

    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    message: str = Field(..., description="Human-readable message")


class TaskResultResponse(BaseModel):
    """Response schema for task results."""

    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[str] = Field(None, description="Task creation timestamp")
    completed_at: Optional[str] = Field(None, description="Task completion timestamp")
