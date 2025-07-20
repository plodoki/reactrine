"""
Background task modules.

Contains all Celery task definitions for the application.
"""

# Import all tasks to make them available when importing app.tasks
from app.tasks.example_task import database_task, error_task, simple_task

__all__ = ["database_task", "error_task", "simple_task"]
