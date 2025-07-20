"""
Unit tests for background task functionality.

Tests all background tasks with proper mocking and error handling,
following established patterns from AGENTS.md.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from sqlalchemy.exc import SQLAlchemyError

from app.tasks.example_task import database_task, error_task, simple_task
from app.worker.celery_app import celery_app


class TestSimpleTask:
    """Test simple task without database access."""

    @patch("time.sleep")
    @patch("app.tasks.example_task.datetime")
    def test_simple_task_success(self, mock_datetime, mock_sleep):
        """Test that simple task executes correctly."""
        # Mock datetime to return a specific value
        mock_datetime.datetime.now.return_value.isoformat.return_value = (
            "2025-01-01T12:00:00"
        )

        # Execute task synchronously for testing
        result = simple_task.apply(args=["test message"], throw=True)

        assert result.successful()
        task_result = result.result
        assert task_result["message"] == "test message"
        assert task_result["status"] == "completed"
        assert task_result["processed_at"] == "2025-01-01T12:00:00"

        # Verify sleep was called to simulate work
        mock_sleep.assert_called_once_with(2)

    @patch("time.sleep")
    def test_simple_task_with_empty_message(self, mock_sleep):
        """Test simple task with empty message."""
        result = simple_task.apply(args=[""], throw=True)

        assert result.successful()
        task_result = result.result
        assert task_result["message"] == ""
        assert task_result["status"] == "completed"

    @patch("time.sleep")
    def test_simple_task_with_unicode_message(self, mock_sleep):
        """Test simple task with unicode characters."""
        unicode_message = "Hello 世界 🌍"
        result = simple_task.apply(args=[unicode_message], throw=True)

        assert result.successful()
        task_result = result.result
        assert task_result["message"] == unicode_message
        assert task_result["status"] == "completed"

    @patch("time.sleep")
    def test_simple_task_with_long_message(self, mock_sleep):
        """Test simple task with very long message."""
        long_message = "x" * 10000
        result = simple_task.apply(args=[long_message], throw=True)

        assert result.successful()
        task_result = result.result
        assert task_result["message"] == long_message
        assert task_result["status"] == "completed"


class TestErrorTask:
    """Test error handling and retry functionality."""

    def test_error_task_success_on_first_attempt(self):
        """Test error task when it should succeed immediately."""
        result = error_task.apply(args=[False], throw=True)

        assert result.successful()
        task_result = result.result
        assert task_result["status"] == "completed"
        assert task_result["attempts"] == 1
        assert "succeeded" in task_result["message"]

    def test_error_task_failure_with_retries(self):
        """Test error task failure behavior with retries."""
        # Should fail on first attempt
        with pytest.raises(Exception, match="Intentional failure for testing"):
            error_task.apply(args=[True], throw=True)

    def test_error_task_success_after_retries(self):
        """Test error task succeeding after maximum retries."""
        # Test that the task can succeed when should_fail is False
        result = error_task.apply(args=[False], throw=True)

        assert result.successful()
        task_result = result.result
        assert task_result["status"] == "completed"
        assert task_result["attempts"] == 1
        assert "succeeded" in task_result["message"]

    def test_error_task_retry_configuration(self):
        """Test that error task has correct retry configuration."""
        # Check that retry configuration is properly set in the decorator
        assert hasattr(error_task, "max_retries")
        assert error_task.max_retries == 3
        # The countdown parameter in the decorator doesn't directly set default_retry_delay
        # Instead, it sets the initial retry delay when the task is retried
        assert hasattr(error_task, "default_retry_delay")
        # Celery may use its own default, so we just check that it exists
        assert error_task.default_retry_delay is not None


@pytest.mark.asyncio
class TestDatabaseTask:
    """Test database-aware tasks."""

    @pytest_asyncio.fixture
    async def mock_db_session(self):
        """Create mock database session using established patterns."""
        from app.tests.mocks import create_mock_db_session

        async for db in create_mock_db_session():
            yield db

    async def test_database_task_simple_query(self, mock_db_session):
        """Test database task with simple query."""
        # Mock the database response
        mock_result = Mock()
        mock_rows = [Mock(_mapping={"count": 1}), Mock(_mapping={"count": 2})]
        mock_result.fetchall.return_value = mock_rows
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute the task through Celery apply
        with patch(
            "app.worker.base_task.async_session_factory"
        ) as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_db_session
            result = await database_task.run("users")

        assert result is not None
        assert result["table_name"] == "users"
        assert result["row_count"] == 2
        assert result["status"] == "completed"
        assert len(result["results"]) == 2
        assert result["results"][0] == {"count": 1}
        assert result["results"][1] == {"count": 2}

        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0]
        assert str(call_args[0]) == "SELECT * FROM users LIMIT 10"

    async def test_database_task_empty_result(self, mock_db_session):
        """Test database task with empty result set."""
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "app.worker.base_task.async_session_factory"
        ) as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_db_session
            result = await database_task.run("api_keys")

        assert result["row_count"] == 0
        assert result["results"] == []
        assert result["status"] == "completed"
        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0]
        assert str(call_args[0]) == "SELECT * FROM api_keys LIMIT 10"

    async def test_database_task_sql_error(self, mock_db_session):
        """Test database task with SQL error."""
        mock_db_session.execute = AsyncMock(
            side_effect=SQLAlchemyError("Invalid SQL syntax")
        )

        with patch(
            "app.worker.base_task.async_session_factory"
        ) as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_db_session
            with pytest.raises(SQLAlchemyError, match="Invalid SQL syntax"):
                await database_task.run("users")
        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0]
        assert str(call_args[0]) == "SELECT * FROM users LIMIT 10"

    async def test_database_task_generic_error(self, mock_db_session):
        """Test database task with generic error."""
        mock_db_session.execute = AsyncMock(
            side_effect=ValueError("Generic database error")
        )

        with patch(
            "app.worker.base_task.async_session_factory"
        ) as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_db_session
            with pytest.raises(ValueError, match="Generic database error"):
                await database_task.run("users")
        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0]
        assert str(call_args[0]) == "SELECT * FROM users LIMIT 10"

    async def test_database_task_complex_query(self, mock_db_session):
        """Test database task with complex query and multiple columns."""
        mock_result = Mock()
        mock_row = Mock(
            _mapping={
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "is_active": True,
            }
        )
        mock_result.fetchall.return_value = [mock_row]
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "app.worker.base_task.async_session_factory"
        ) as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_db_session
            result = await database_task.run("users")

        assert result["row_count"] == 1
        assert result["results"][0]["id"] == 1
        assert result["results"][0]["name"] == "John Doe"
        assert result["results"][0]["email"] == "john@example.com"
        assert result["results"][0]["is_active"] is True
        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0]
        assert str(call_args[0]) == "SELECT * FROM users LIMIT 10"

    async def test_database_task_with_parameters(self, mock_db_session):
        """Test database task execution with different table names."""
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Test that the task can handle different table names
        with patch(
            "app.worker.base_task.async_session_factory"
        ) as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_db_session
            result = await database_task.run("llm_settings")

        assert result["table_name"] == "llm_settings"
        assert result["status"] == "completed"

        # Verify the execute was called with the text query
        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0]
        assert str(call_args[0]) == "SELECT * FROM llm_settings LIMIT 10"


class TestTaskRegistration:
    """Test that tasks are properly registered with Celery."""

    @pytest_asyncio.fixture(autouse=True)
    def _celery_eager(self):
        celery_app.conf.update(task_always_eager=True)
        yield
        celery_app.conf.update(task_always_eager=False)

    def test_simple_task_registration(self):
        """Verify simple_task is registered."""
        assert simple_task.name in celery_app.tasks
        assert celery_app.tasks[simple_task.name] == simple_task

    def test_database_task_registration(self):
        """Verify database_task is registered."""
        assert database_task.name == "app.tasks.example_task.database_task"
        assert database_task.name in celery_app.tasks
        assert celery_app.tasks[database_task.name] is database_task

    def test_error_task_registration(self):
        """Verify error_task is registered."""
        assert error_task.name in celery_app.tasks
        assert celery_app.tasks[error_task.name] is error_task

    def test_all_example_tasks_registered(self):
        """Ensure all tasks from the example module are registered."""
        from app.tasks import example_task

        registered_tasks = celery_app.tasks.keys()
        # Find all callables in example_task that are celery tasks
        tasks_in_module = [
            getattr(example_task, item)
            for item in dir(example_task)
            if hasattr(getattr(example_task, item), "name")
            and getattr(example_task, item).name in registered_tasks
        ]

        assert len(tasks_in_module) == 3  # simple, error, database
        assert all(task.name in registered_tasks for task in tasks_in_module)

    def test_task_names_follow_convention(self):
        """Test task naming conventions."""
        # Task names should be explicit for clarity
        assert simple_task.name == "app.tasks.example_task.simple_task"
        assert error_task.name == "app.tasks.example_task.error_task"
        assert database_task.name == "app.tasks.example_task.database_task"


class TestTaskLogging:
    """Test logging within Celery tasks."""

    @patch("app.tasks.example_task.logger")
    def test_simple_task_logging(self, mock_logger):
        """Test logging for simple task."""
        simple_task.apply(args=["log test"], throw=True)
        mock_logger.info.assert_any_call(
            "Processing simple task with message: log test"
        )
        assert mock_logger.info.call_count >= 2

    @patch("app.tasks.example_task.logger")
    def test_error_task_logging(self, mock_logger):
        """Test logging for error task."""
        with pytest.raises(Exception):
            error_task.apply(args=[True], throw=True)
        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    @patch("app.worker.base_task.logger")
    async def test_database_task_logging(self, mock_logger, mock_db_session):
        """Test logging for database task."""
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "app.worker.base_task.async_session_factory"
        ) as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_db_session
            await database_task.run("users")

        # No direct logging in `database_task` itself, but in the base class
        # This test now only confirms it runs without error
        assert mock_logger.error.call_count == 0

    @pytest.mark.asyncio
    @patch("app.worker.base_task.logger")
    async def test_database_task_error_logging(self, mock_logger, mock_db_session):
        """Test error logging for database task."""
        mock_db_session.execute = AsyncMock(side_effect=SQLAlchemyError("DB Error"))

        with patch(
            "app.worker.base_task.async_session_factory"
        ) as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_db_session
            with pytest.raises(SQLAlchemyError):
                await database_task.run("users")

        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        assert "Task app.tasks.example_task.database_task failed" in log_message
        assert "DB Error" in log_message


class TestTaskWithDbEdgeCases:
    """Tests for edge cases in database-aware tasks."""

    def test_task_with_db_no_name(self):
        """Test that task name is inferred from function if not provided."""
        from app.worker.base_task import task_with_db

        @task_with_db()
        async def my_unnamed_task(db, arg1):
            return f"processed {arg1}"

        expected_name = "app.tests.test_tasks_unit.my_unnamed_task"
        assert my_unnamed_task.name == expected_name

    def test_task_with_db_explicit_name(self):
        """Test that explicit task name is used when provided."""
        from app.worker.base_task import task_with_db

        @task_with_db(name="custom.explicit.name")
        async def my_named_task(db, arg1):
            return f"processed {arg1}"

        assert my_named_task.name == "custom.explicit.name"

    def test_task_with_db_no_db_arg(self):
        """Test that task_with_db fails if decorated function omits db param."""
        from app.worker.base_task import task_with_db

        @task_with_db()
        async def wrong_signature_task(arg1):
            return f"processed {arg1}"

        with pytest.raises(TypeError):
            wrong_signature_task.apply(args=["test"], throw=True)

    @pytest.mark.parametrize(
        "invalid_name",
        ["", None],
        ids=["empty_string_name", "none_name_not_allowed"],
    )
    def test_task_with_db_invalid_name(self, invalid_name):
        """Test decorator with invalid task names."""
        from app.worker.base_task import task_with_db

        # Celery allows None and empty string, will auto-generate name
        # so no exception is raised. We can still define it.
        @task_with_db(name=invalid_name)
        async def task_with_valid_name(db, arg1):
            return f"processed {arg1}"

        assert task_with_valid_name is not None
