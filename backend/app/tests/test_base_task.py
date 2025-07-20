"""
Tests for DatabaseTask base class and task_with_db decorator.

Tests the database task infrastructure with proper mocking and error handling,
following established patterns from AGENTS.md.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.worker.base_task import DatabaseTask, task_with_db
from app.worker.celery_app import celery_app


class TestDatabaseTask:
    """Test DatabaseTask base class functionality."""

    def test_database_task_initialization(self):
        """Test that DatabaseTask can be initialized."""
        task = DatabaseTask()
        assert task is not None
        assert isinstance(task, DatabaseTask)

    def test_database_task_run_with_db_not_implemented(self):
        """Test that run_with_db raises NotImplementedError."""
        task = DatabaseTask()

        with pytest.raises(
            NotImplementedError, match="Subclasses must implement run_with_db"
        ):
            asyncio.run(task.run_with_db())

    @patch("app.worker.base_task.async_session_factory")
    def test_database_task_call_with_sync_function(self, mock_session_factory):
        """Test DatabaseTask.__call__ with synchronous function."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        class TestTask(DatabaseTask):
            def run(self, *args, **kwargs):
                return "sync_result"

        task = TestTask()
        result = task(*[], **{})

        assert result == "sync_result"

    @patch("app.worker.base_task.async_session_factory")
    def test_database_task_call_with_async_function(self, mock_session_factory):
        """Test DatabaseTask.__call__ with asynchronous function."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        class TestTask(DatabaseTask):
            async def run(self, *args, **kwargs):
                return "async_result"

        task = TestTask()
        result = task(*[], **{})

        assert result == "async_result"

    @patch("app.worker.base_task.async_session_factory")
    @patch("app.worker.base_task.logger")
    def test_database_task_run_success(self, mock_logger, mock_session_factory):
        """Test successful database task execution."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        class TestTask(DatabaseTask):
            name = "test_task"

            async def run_with_db(self, session, *args, **kwargs):
                return {"result": "success"}

        task = TestTask()
        result = asyncio.run(task.run())

        assert result == {"result": "success"}
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("app.worker.base_task.async_session_factory")
    @patch("app.worker.base_task.logger")
    def test_database_task_run_with_exception(self, mock_logger, mock_session_factory):
        """Test database task execution with exception."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        class TestTask(DatabaseTask):
            name = "test_task"

            async def run_with_db(self, session, *args, **kwargs):
                raise SQLAlchemyError("Database error")

        task = TestTask()

        with pytest.raises(SQLAlchemyError, match="Database error"):
            asyncio.run(task.run())

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_logger.error.assert_called_once_with(
            "Task test_task failed: Database error"
        )

    @patch("app.worker.base_task.async_session_factory")
    def test_database_task_run_with_generic_error(self, mock_session_factory):
        """Test database task execution with generic error."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        class TestTask(DatabaseTask):
            name = "test_task"

            async def run_with_db(self, session, *args, **kwargs):
                raise ValueError("Generic error")

        task = TestTask()

        with pytest.raises(ValueError, match="Generic error"):
            asyncio.run(task.run())

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("app.worker.base_task.async_session_factory")
    def test_database_task_run_with_integrity_error(self, mock_session_factory):
        """Test database task execution with integrity error."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        class TestTask(DatabaseTask):
            name = "test_task"

            async def run_with_db(self, session, *args, **kwargs):
                raise IntegrityError("Constraint violation", None, None)

        task = TestTask()

        with pytest.raises(IntegrityError, match="Constraint violation"):
            asyncio.run(task.run())

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("app.worker.base_task.async_session_factory")
    def test_database_task_session_management(self, mock_session_factory):
        """Test that database session is properly managed."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        class TestTask(DatabaseTask):
            async def run_with_db(self, session, *args, **kwargs):
                # Verify session is passed correctly
                assert session is mock_session
                return "success"

        task = TestTask()
        result = asyncio.run(task.run())

        assert result == "success"
        # Verify session lifecycle
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("app.worker.base_task.async_session_factory")
    def test_database_task_with_args_and_kwargs(self, mock_session_factory):
        """Test database task with arguments and keyword arguments."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        class TestTask(DatabaseTask):
            async def run_with_db(self, session, arg1, arg2, kwarg1=None, kwarg2=None):
                return {"arg1": arg1, "arg2": arg2, "kwarg1": kwarg1, "kwarg2": kwarg2}

        task = TestTask()
        result = asyncio.run(task.run("value1", "value2", kwarg1="kw1", kwarg2="kw2"))

        expected = {
            "arg1": "value1",
            "arg2": "value2",
            "kwarg1": "kw1",
            "kwarg2": "kw2",
        }
        assert result == expected


class TestTaskWithDbDecorator:
    """Test task_with_db decorator functionality."""

    def test_task_with_db_decorator_basic(self):
        """Test basic task_with_db decorator usage."""

        @task_with_db(name="test_decorator_task")
        async def test_task(db: AsyncSession, message: str) -> str:
            return f"processed: {message}"

        # Verify task is registered
        assert "test_decorator_task" in celery_app.tasks
        task = celery_app.tasks["test_decorator_task"]
        assert task.name == "test_decorator_task"

    def test_task_with_db_decorator_auto_name(self):
        """Test task_with_db decorator with automatic name generation."""

        @task_with_db()
        async def auto_named_task(db: AsyncSession) -> str:
            return "auto_named"

        # Should generate name from module and function name
        # The actual name will be the full module path + function name
        task_names = list(celery_app.tasks.keys())
        auto_named_tasks = [name for name in task_names if "auto_named_task" in name]
        assert len(auto_named_tasks) >= 1, f"Auto named task not found in {task_names}"

    def test_task_with_db_decorator_with_celery_kwargs(self):
        """Test task_with_db decorator with additional Celery kwargs."""

        @task_with_db(name="test_kwargs_task", bind=True, max_retries=5)
        async def test_task_with_kwargs(db: AsyncSession) -> str:
            return "with_kwargs"

        assert "test_kwargs_task" in celery_app.tasks
        task = celery_app.tasks["test_kwargs_task"]
        assert task.name == "test_kwargs_task"

    @patch("app.worker.base_task.async_session_factory")
    def test_task_with_db_decorator_execution(self, mock_session_factory):
        """Test execution of task created with task_with_db decorator."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        @task_with_db(name="test_execution_task")
        async def test_execution(db: AsyncSession, value: str) -> dict:
            return {"db_session": db is mock_session, "value": value}

        # Execute task synchronously for testing
        result = test_execution.apply(args=["test_value"], throw=True)

        assert result.successful()
        task_result = result.result
        assert task_result["db_session"] is True
        assert task_result["value"] == "test_value"

        # Verify session management
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("app.worker.base_task.async_session_factory")
    def test_task_with_db_decorator_exception_handling(self, mock_session_factory):
        """Test exception handling in task created with task_with_db decorator."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        @task_with_db(name="test_exception_task")
        async def test_exception(db: AsyncSession) -> str:
            raise SQLAlchemyError("Test error")

        with pytest.raises(SQLAlchemyError, match="Test error"):
            test_exception.apply(args=[], throw=True)

        # Verify session rollback
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_task_with_db_decorator_multiple_tasks(self):
        """Test creating multiple tasks with task_with_db decorator."""

        @task_with_db(name="task_one")
        async def task_one(db: AsyncSession) -> str:
            return "one"

        @task_with_db(name="task_two")
        async def task_two(db: AsyncSession) -> str:
            return "two"

        @task_with_db(name="task_three")
        async def task_three(db: AsyncSession) -> str:
            return "three"

        # Verify all tasks are registered with correct names
        assert task_one.name == "task_one"
        assert task_two.name == "task_two"
        assert task_three.name == "task_three"

        # Verify tasks are distinct objects
        assert task_one is not task_two
        assert task_two is not task_three
        assert task_one is not task_three

    @patch("app.worker.base_task.async_session_factory")
    def test_task_with_db_decorator_complex_args(self, mock_session_factory):
        """Test task_with_db decorator with complex arguments."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        @task_with_db(name="complex_args_task")
        async def complex_task(
            db: AsyncSession,
            user_id: int,
            data: dict,
            options: list | None = None,
            **kwargs,
        ) -> dict:
            return {
                "user_id": user_id,
                "data": data,
                "options": options or [],
                "kwargs": kwargs,
                "has_db": db is mock_session,
            }

        result = complex_task.apply(
            args=[42, {"key": "value"}],
            kwargs={"options": ["opt1", "opt2"], "extra": "data"},
            throw=True,
        )

        assert result.successful()
        task_result = result.result
        assert task_result["user_id"] == 42
        assert task_result["data"] == {"key": "value"}
        assert task_result["options"] == ["opt1", "opt2"]
        assert task_result["kwargs"] == {"extra": "data"}
        assert task_result["has_db"] is True

    def test_task_with_db_decorator_return_value(self):
        """Test that task_with_db decorator returns the correct task object."""

        @task_with_db(name="return_value_task")
        async def return_value_task(db: AsyncSession) -> str:
            return "test"

        # The decorator should return a task object that has a delay method
        assert hasattr(return_value_task, "delay")
        assert hasattr(return_value_task, "apply")
        assert hasattr(return_value_task, "apply_async")

        # Verify it's the correct task
        assert return_value_task.name == "return_value_task"

    @patch("app.worker.base_task.async_session_factory")
    def test_task_with_db_decorator_async_context_manager(self, mock_session_factory):
        """Test that task_with_db decorator properly handles async context manager."""
        mock_session = AsyncMock()
        mock_async_session = AsyncMock()
        mock_async_session.__aenter__.return_value = mock_session
        mock_async_session.__aexit__.return_value = None
        mock_session_factory.return_value = mock_async_session

        @task_with_db(name="context_manager_task")
        async def context_task(db: AsyncSession) -> str:
            return "context_success"

        result = context_task.apply(args=[], throw=True)

        assert result.successful()
        assert result.result == "context_success"

        # Verify async context manager was used properly
        mock_async_session.__aenter__.assert_called_once()
        mock_async_session.__aexit__.assert_called_once()

    def test_task_with_db_decorator_inheritance(self):
        """Test that tasks created with task_with_db inherit from DatabaseTask."""

        @task_with_db(name="inheritance_task")
        async def inheritance_task(db: AsyncSession) -> str:
            return "inherited"

        # The task should be an instance of DatabaseTask
        assert isinstance(inheritance_task, DatabaseTask)
        assert hasattr(inheritance_task, "run_with_db")
        assert hasattr(inheritance_task, "run")


class TestTaskWithDbEdgeCases:
    """Test edge cases and error conditions for task_with_db decorator."""

    def test_task_with_db_empty_name(self):
        """Test task_with_db decorator with empty name."""

        @task_with_db(name="")
        async def empty_name_task(db: AsyncSession) -> str:
            return "empty_name"

        # Should register the task with the function name
        assert empty_name_task.name == "app.tests.test_base_task.empty_name_task"

    def test_task_with_db_none_name(self):
        """Test task_with_db decorator with None as name."""

        @task_with_db(name=None)
        async def none_name_task(db: AsyncSession) -> str:
            return "none_name"

        expected_name = "app.tests.test_base_task.none_name_task"
        assert none_name_task.name == expected_name

    def test_task_with_db_duplicate_names(self):
        """Test that tasks with duplicate names can be registered."""

        @task_with_db(name="duplicate_task")
        async def first_duplicate(db: AsyncSession) -> str:
            return "first"

        @task_with_db(name="duplicate_task")
        async def second_duplicate(db: AsyncSession) -> str:
            return "second"

        # The second task should overwrite the first
        assert first_duplicate.name == "duplicate_task"
        assert second_duplicate.name == "duplicate_task"

    @patch("app.worker.base_task.async_session_factory")
    def test_task_with_db_no_return_value(self, mock_session_factory):
        """Test task_with_db decorator with function that returns None."""
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        @task_with_db(name="no_return_task")
        async def no_return_task(db: AsyncSession) -> None:
            # Function that doesn't return anything
            pass

        result = no_return_task.apply(args=[], throw=True)

        assert result.successful()
        assert result.result is None
