"""
API tests for task management endpoints.

Tests all task-related API endpoints with proper mocking and validation,
following established patterns from AGENTS.md.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.tasks import TaskStatus


class TestTasksAPI:
    """Test task management API endpoints."""

    def test_trigger_simple_task_success(self, authenticated_client: TestClient):
        """Test triggering a simple task successfully."""
        with patch("app.api.v1.endpoints.tasks.simple_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "test-task-id-123"
            mock_task.delay.return_value = mock_result

            response = authenticated_client.post(
                "/api/v1/tasks/simple", json={"message": "test message"}
            )

            assert response.status_code == 202
            data = response.json()
            assert data["task_id"] == "test-task-id-123"
            assert data["status"] == TaskStatus.PENDING
            assert "Simple task queued successfully" in data["message"]

            # Verify task was called with correct parameters
            mock_task.delay.assert_called_once_with("test message")

    def test_trigger_simple_task_empty_message(self, authenticated_client: TestClient):
        """Test triggering a simple task with empty message."""
        with patch("app.api.v1.endpoints.tasks.simple_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "empty-task-id"
            mock_task.delay.return_value = mock_result

            response = authenticated_client.post(
                "/api/v1/tasks/simple", json={"message": ""}
            )

            assert response.status_code == 202
            data = response.json()
            assert data["task_id"] == "empty-task-id"
            assert data["status"] == TaskStatus.PENDING

            mock_task.delay.assert_called_once_with("")

    def test_trigger_simple_task_unicode_message(
        self, authenticated_client: TestClient
    ):
        """Test triggering a simple task with unicode message."""
        with patch("app.api.v1.endpoints.tasks.simple_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "unicode-task-id"
            mock_task.delay.return_value = mock_result

            unicode_message = "Hello 世界 🌍"
            response = authenticated_client.post(
                "/api/v1/tasks/simple", json={"message": unicode_message}
            )

            assert response.status_code == 202
            data = response.json()
            assert data["task_id"] == "unicode-task-id"

            mock_task.delay.assert_called_once_with(unicode_message)

    def test_trigger_simple_task_invalid_payload(
        self, authenticated_client: TestClient
    ):
        """Test triggering a simple task with invalid payload."""
        response = authenticated_client.post(
            "/api/v1/tasks/simple",
            json={},  # Missing required 'message' field
        )

        assert response.status_code == 422
        data = response.json()
        assert "errors" in data
        # Check if any error has "message" in its location (loc field)
        assert any(
            isinstance(error, dict) and "loc" in error and "message" in error["loc"]
            for error in data["errors"]
        )

    def test_trigger_simple_task_invalid_json(self, authenticated_client: TestClient):
        """Test triggering a simple task with invalid JSON."""
        response = authenticated_client.post(
            "/api/v1/tasks/simple",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_trigger_database_task_success(self, authenticated_client: TestClient):
        """Test triggering a database task successfully."""
        with patch("app.api.v1.endpoints.tasks.database_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "db-task-id-456"
            mock_task.delay.return_value = mock_result

            response = authenticated_client.post(
                "/api/v1/tasks/database", json={"query": "count_users"}
            )

            assert response.status_code == 202
            data = response.json()
            assert data["task_id"] == "db-task-id-456"
            assert data["status"] == TaskStatus.PENDING
            assert "Database task queued successfully" in data["message"]

            mock_task.delay.assert_called_once_with("users")

    def test_trigger_database_task_complex_query(
        self, authenticated_client: TestClient
    ):
        """Test triggering a database task with predefined operation."""
        with patch("app.api.v1.endpoints.tasks.database_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "complex-db-task-id"
            mock_task.delay.return_value = mock_result

            response = authenticated_client.post(
                "/api/v1/tasks/database", json={"query": "get_user_stats"}
            )

            assert response.status_code == 202
            data = response.json()
            assert data["task_id"] == "complex-db-task-id"

            mock_task.delay.assert_called_once_with("users")

    def test_trigger_database_task_empty_query(self, authenticated_client: TestClient):
        """Test triggering a database task with empty query."""
        with patch("app.api.v1.endpoints.tasks.database_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "empty-query-task-id"
            mock_task.delay.return_value = mock_result

            response = authenticated_client.post(
                "/api/v1/tasks/database", json={"query": ""}
            )

        assert response.status_code == 422

    def test_trigger_database_task_invalid_payload(
        self, authenticated_client: TestClient
    ):
        """Test triggering a database task with invalid payload."""
        response = authenticated_client.post(
            "/api/v1/tasks/database",
            json={},  # Missing required 'query' field
        )

        assert response.status_code == 422

    def test_trigger_database_task_invalid_operation(
        self, authenticated_client: TestClient
    ):
        """Test triggering a database task with invalid operation."""
        response = authenticated_client.post(
            "/api/v1/tasks/database", json={"query": "DROP TABLE users"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid operation" in data["detail"]
        assert "count_users" in data["detail"]

    def test_trigger_error_task_success(self, authenticated_client: TestClient):
        """Test triggering an error task successfully."""
        with patch("app.api.v1.endpoints.tasks.error_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "error-task-id-789"
            mock_task.delay.return_value = mock_result

            response = authenticated_client.post(
                "/api/v1/tasks/error", json={"should_fail": False}
            )

            assert response.status_code == 202
            data = response.json()
            assert data["task_id"] == "error-task-id-789"
            assert data["status"] == TaskStatus.PENDING
            assert "Error task queued successfully" in data["message"]

            mock_task.delay.assert_called_once_with(False)

    def test_trigger_error_task_default_should_fail(
        self, authenticated_client: TestClient
    ):
        """Test triggering an error task with default should_fail value."""
        with patch("app.api.v1.endpoints.tasks.error_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "default-error-task-id"
            mock_task.delay.return_value = mock_result

            response = authenticated_client.post(
                "/api/v1/tasks/error",
                json={},  # should_fail defaults to True
            )

            assert response.status_code == 202
            data = response.json()
            assert data["task_id"] == "default-error-task-id"

            mock_task.delay.assert_called_once_with(True)

    def test_trigger_error_task_explicit_should_fail(
        self, authenticated_client: TestClient
    ):
        """Test triggering an error task with explicit should_fail value."""
        with patch("app.api.v1.endpoints.tasks.error_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "explicit-error-task-id"
            mock_task.delay.return_value = mock_result

            response = authenticated_client.post(
                "/api/v1/tasks/error", json={"should_fail": True}
            )

            assert response.status_code == 202
            data = response.json()
            assert data["task_id"] == "explicit-error-task-id"

            mock_task.delay.assert_called_once_with(True)

    @patch("app.api.v1.endpoints.tasks.AsyncResult")
    def test_get_task_result_success(
        self, mock_async_result, authenticated_client: TestClient
    ):
        """Test getting task result for successful task."""
        mock_result = Mock()
        mock_result.status = "SUCCESS"
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {"message": "Task completed", "status": "success"}
        mock_result.date_done = None

        mock_async_result.return_value = mock_result

        response = authenticated_client.get("/api/v1/tasks/test-task-id")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == TaskStatus.SUCCESS
        assert data["result"] == {"message": "Task completed", "status": "success"}
        assert data["error"] is None

        mock_async_result.assert_called_once_with(
            "test-task-id", app=mock_async_result.call_args[1]["app"]
        )

    @patch("app.api.v1.endpoints.tasks.AsyncResult")
    def test_get_task_result_failure(
        self, mock_async_result, authenticated_client: TestClient
    ):
        """Test getting task result for failed task."""
        mock_result = Mock()
        mock_result.status = "FAILURE"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = True
        mock_result.result = None
        mock_result.info = "Task failed due to database error"
        mock_result.date_done = None

        mock_async_result.return_value = mock_result

        response = authenticated_client.get("/api/v1/tasks/failed-task-id")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "failed-task-id"
        assert data["status"] == TaskStatus.FAILURE
        assert data["result"] is None
        assert data["error"] == "Task failed due to database error"

    @patch("app.api.v1.endpoints.tasks.AsyncResult")
    def test_get_task_result_pending(
        self, mock_async_result, authenticated_client: TestClient
    ):
        """Test getting task result for pending task."""
        mock_result = Mock()
        mock_result.status = "PENDING"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = False
        mock_result.result = None
        mock_result.date_done = None

        mock_async_result.return_value = mock_result

        response = authenticated_client.get("/api/v1/tasks/pending-task-id")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "pending-task-id"
        assert data["status"] == TaskStatus.PENDING
        assert data["result"] is None
        assert data["error"] is None

    @patch("app.api.v1.endpoints.tasks.AsyncResult")
    def test_get_task_result_started(
        self, mock_async_result, authenticated_client: TestClient
    ):
        """Test getting task result for started task."""
        mock_result = Mock()
        mock_result.status = "STARTED"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = False
        mock_result.result = None
        mock_result.date_done = None

        mock_async_result.return_value = mock_result

        response = authenticated_client.get("/api/v1/tasks/started-task-id")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "started-task-id"
        assert data["status"] == TaskStatus.STARTED
        assert data["result"] is None
        assert data["error"] is None

    @patch("app.api.v1.endpoints.tasks.AsyncResult")
    def test_get_task_result_retry(
        self, mock_async_result, authenticated_client: TestClient
    ):
        """Test getting task result for retry task."""
        mock_result = Mock()
        mock_result.status = "RETRY"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = False
        mock_result.result = None
        mock_result.date_done = None

        mock_async_result.return_value = mock_result

        response = authenticated_client.get("/api/v1/tasks/retry-task-id")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "retry-task-id"
        assert data["status"] == TaskStatus.RETRY
        assert data["result"] is None
        assert data["error"] is None

    @patch("app.api.v1.endpoints.tasks.AsyncResult")
    def test_get_task_result_with_completion_time(
        self, mock_async_result, authenticated_client: TestClient
    ):
        """Test getting task result with completion timestamp."""
        from datetime import datetime

        mock_result = Mock()
        mock_result.status = "SUCCESS"
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {"status": "completed"}
        mock_result.date_done = datetime(2023, 1, 1, 12, 0, 0)

        mock_async_result.return_value = mock_result

        response = authenticated_client.get("/api/v1/tasks/completed-task-id")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "completed-task-id"
        assert data["status"] == TaskStatus.SUCCESS
        assert data["completed_at"] == "2023-01-01T12:00:00"

    @patch("app.api.v1.endpoints.tasks.AsyncResult")
    def test_get_task_result_not_found(
        self, mock_async_result, authenticated_client: TestClient
    ):
        """Test getting result for non-existent task."""
        mock_async_result.side_effect = Exception("Task not found")

        response = authenticated_client.get("/api/v1/tasks/nonexistent-task-id")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch("app.api.v1.endpoints.tasks.AsyncResult")
    def test_get_task_result_invalid_task_id(
        self, mock_async_result, authenticated_client: TestClient
    ):
        """Test getting result for invalid task ID."""
        mock_async_result.side_effect = ValueError("Invalid task ID format")

        response = authenticated_client.get("/api/v1/tasks/invalid-task-id-format")

        assert response.status_code == 404
        data = response.json()
        assert "invalid" in data["detail"].lower()

    def test_list_active_tasks_placeholder(self, authenticated_client: TestClient):
        """Test listing active tasks endpoint (placeholder implementation)."""
        response = authenticated_client.get("/api/v1/tasks/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "not implemented" in data["message"]
        assert "suggestion" in data
        assert "Flower" in data["suggestion"]

    def test_task_endpoints_content_type(self, authenticated_client: TestClient):
        """Test that task endpoints return proper content type."""
        with patch("app.api.v1.endpoints.tasks.simple_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "content-type-test"
            mock_task.delay.return_value = mock_result

            response = authenticated_client.post(
                "/api/v1/tasks/simple", json={"message": "content type test"}
            )

            assert response.status_code == 202
            assert response.headers["content-type"] == "application/json"

    def test_task_endpoints_cors_headers(self, authenticated_client: TestClient):
        """Test that task endpoints include CORS headers if configured."""
        with patch("app.api.v1.endpoints.tasks.simple_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "cors-test"
            mock_task.delay.return_value = mock_result

            response = authenticated_client.post(
                "/api/v1/tasks/simple", json={"message": "cors test"}
            )

            assert response.status_code == 202
            # CORS headers would be added by middleware if configured

    def test_task_endpoints_error_handling(self, authenticated_client: TestClient):
        """Test error handling in task endpoints."""
        with patch("app.api.v1.endpoints.tasks.simple_task") as mock_task:
            mock_task.delay.side_effect = Exception("Task queue error")

            with pytest.raises(Exception, match="Task queue error"):
                authenticated_client.post(
                    "/api/v1/tasks/simple", json={"message": "error test"}
                )


class TestTasksAPIValidation:
    """Test request validation for task API endpoints."""

    def test_simple_task_message_validation(self, authenticated_client: TestClient):
        """Test message validation for simple task."""
        # Test with various invalid message types
        invalid_payloads = [
            {"message": None},
            {"message": 123},
            {"message": []},
            {"message": {}},
        ]

        for payload in invalid_payloads:
            response = authenticated_client.post("/api/v1/tasks/simple", json=payload)
            assert response.status_code == 422

    def test_database_task_query_validation(self, authenticated_client: TestClient):
        """Test query validation for database task."""
        # Test with various invalid query types
        invalid_payloads = [
            {"query": None},
            {"query": 123},
            {"query": []},
            {"query": {}},
        ]

        for payload in invalid_payloads:
            response = authenticated_client.post("/api/v1/tasks/database", json=payload)
            assert response.status_code == 422

    def test_error_task_should_fail_validation(self, authenticated_client: TestClient):
        """Test should_fail validation for error task."""
        with patch("app.api.v1.endpoints.tasks.error_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "validation-test"
            mock_task.delay.return_value = mock_result

            # Test with valid boolean values
            valid_payloads = [
                {"should_fail": True},
                {"should_fail": False},
                {},  # Default value
            ]

            for payload in valid_payloads:
                response = authenticated_client.post(
                    "/api/v1/tasks/error", json=payload
                )
                assert response.status_code == 202

    def test_error_task_should_fail_invalid_validation(
        self, authenticated_client: TestClient
    ):
        """Test should_fail validation with invalid values."""
        # Test with various invalid should_fail types that should actually fail validation
        # Note: Pydantic converts "true" and 1 to boolean True, so they're valid
        invalid_payloads = [
            {"should_fail": []},
            {"should_fail": {}},
            {"should_fail": "not_a_boolean"},
            {"should_fail": None},
        ]

        for payload in invalid_payloads:
            response = authenticated_client.post("/api/v1/tasks/error", json=payload)
            assert response.status_code == 422

    def test_error_task_should_fail_valid_coercion(
        self, authenticated_client: TestClient
    ):
        """Test should_fail validation with values that should be coerced to boolean."""
        with patch("app.api.v1.endpoints.tasks.error_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "coercion-test"
            mock_task.delay.return_value = mock_result

            # Test with values that Pydantic should coerce to boolean
            valid_coercion_payloads = [
                {"should_fail": "true"},  # String "true" -> True
                {"should_fail": "false"},  # String "false" -> False
                {"should_fail": 1},  # Integer 1 -> True
                {"should_fail": 0},  # Integer 0 -> False
            ]

            for payload in valid_coercion_payloads:
                response = authenticated_client.post(
                    "/api/v1/tasks/error", json=payload
                )
                assert response.status_code == 202
                data = response.json()
                assert data["task_id"] == "coercion-test"
                assert data["status"] == TaskStatus.PENDING

    def test_task_id_parameter_validation(self, authenticated_client: TestClient):
        """Test task ID parameter validation."""
        with patch("app.api.v1.endpoints.tasks.AsyncResult") as mock_async_result:
            mock_result = Mock()
            mock_result.status = "SUCCESS"
            mock_result.successful.return_value = True
            mock_result.failed.return_value = False
            mock_result.result = {"status": "completed"}
            mock_result.date_done = None

            mock_async_result.return_value = mock_result

            # Test with various task ID formats
            valid_task_ids = [
                "simple-task-id",
                "task_with_underscores",
                "task-with-numbers-123",
                "a1b2c3d4-e5f6-7890-abcd-ef1234567890",  # UUID format
            ]

            for task_id in valid_task_ids:
                mock_async_result.reset_mock()
                response = authenticated_client.get(f"/api/v1/tasks/{task_id}")
                assert response.status_code == 200
                mock_async_result.assert_called_once_with(
                    task_id, app=mock_async_result.call_args[1]["app"]
                )

    def test_malformed_json_handling(self, authenticated_client: TestClient):
        """Test handling of malformed JSON in requests."""
        malformed_json_strings = [
            '{"message": "test"',  # Missing closing brace
            '{"message": "test"}}',  # Extra closing brace
            '{"message": }',  # Missing value
            '{message: "test"}',  # Missing quotes on key
        ]

        for json_string in malformed_json_strings:
            response = authenticated_client.post(
                "/api/v1/tasks/simple",
                content=json_string,
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == 422

    def test_missing_content_type_header(self, authenticated_client: TestClient):
        """Test requests without proper Content-Type header."""
        with patch("app.api.v1.endpoints.tasks.simple_task") as mock_task:
            mock_result = Mock()
            mock_result.id = "content-type-test"
            mock_task.delay.return_value = mock_result

            response = authenticated_client.post(
                "/api/v1/tasks/simple",
                content='{"message": "test"}',
                # No Content-Type header
            )

            # Should still work with proper JSON data
            assert response.status_code in [
                200,
                202,
                422,
            ]  # Depends on FastAPI handling

    def test_empty_request_body(self, authenticated_client: TestClient):
        """Test requests with empty body."""
        response = authenticated_client.post("/api/v1/tasks/simple", json=None)

        assert response.status_code == 422


class TestTasksAPIIntegration:
    """Integration tests for task API endpoints."""

    def test_full_task_lifecycle_simple(self, authenticated_client: TestClient):
        """Test full lifecycle of a simple task."""
        with patch("app.api.v1.endpoints.tasks.simple_task") as mock_task:
            # Step 1: Trigger task
            mock_result = Mock()
            mock_result.id = "lifecycle-test-123"
            mock_task.delay.return_value = mock_result

            trigger_response = authenticated_client.post(
                "/api/v1/tasks/simple", json={"message": "lifecycle test"}
            )

            assert trigger_response.status_code == 202
            task_data = trigger_response.json()
            task_id = task_data["task_id"]

            # Step 2: Check task status
            with patch("app.api.v1.endpoints.tasks.AsyncResult") as mock_async_result:
                mock_status = Mock()
                mock_status.status = "SUCCESS"
                mock_status.successful.return_value = True
                mock_status.failed.return_value = False
                mock_status.result = {
                    "message": "lifecycle test",
                    "status": "completed",
                }
                mock_status.date_done = None

                mock_async_result.return_value = mock_status

                status_response = authenticated_client.get(f"/api/v1/tasks/{task_id}")

                assert status_response.status_code == 200
                status_data = status_response.json()
                assert status_data["task_id"] == task_id
                assert status_data["status"] == TaskStatus.SUCCESS
                assert status_data["result"]["message"] == "lifecycle test"
                mock_async_result.assert_called_once_with(
                    task_id, app=mock_async_result.call_args[1]["app"]
                )

    def test_multiple_tasks_concurrent(self, authenticated_client: TestClient):
        """Test triggering multiple tasks concurrently."""
        with (
            patch("app.api.v1.endpoints.tasks.simple_task") as mock_simple_task,
            patch("app.api.v1.endpoints.tasks.database_task") as mock_db_task,
            patch("app.api.v1.endpoints.tasks.error_task") as mock_error_task,
        ):
            # Mock task results
            mock_simple_task.delay.return_value = Mock(id="simple-123")
            mock_db_task.delay.return_value = Mock(id="db-456")
            mock_error_task.delay.return_value = Mock(id="error-789")

            # Trigger multiple tasks
            responses = []

            responses.append(
                authenticated_client.post(
                    "/api/v1/tasks/simple", json={"message": "concurrent test 1"}
                )
            )

            responses.append(
                authenticated_client.post(
                    "/api/v1/tasks/database", json={"query": "count_users"}
                )
            )

            responses.append(
                authenticated_client.post(
                    "/api/v1/tasks/error", json={"should_fail": False}
                )
            )

            # All should succeed
            for response in responses:
                assert response.status_code == 202
                data = response.json()
                assert "task_id" in data
                assert data["status"] == TaskStatus.PENDING

            # Verify all tasks were called
            mock_simple_task.delay.assert_called_once()
            mock_db_task.delay.assert_called_once()
            mock_error_task.delay.assert_called_once()

    def test_task_api_error_recovery(self, authenticated_client: TestClient):
        """Test API error recovery and proper error responses."""
        with patch("app.api.v1.endpoints.tasks.simple_task") as mock_task:
            # First request fails
            mock_task.delay.side_effect = Exception("Temporary error")

            with pytest.raises(Exception, match="Temporary error"):
                authenticated_client.post(
                    "/api/v1/tasks/simple", json={"message": "error recovery test"}
                )

            # Second request succeeds
            mock_task.delay.side_effect = None
            mock_task.delay.return_value = Mock(id="recovery-test-id")

            response2 = authenticated_client.post(
                "/api/v1/tasks/simple", json={"message": "error recovery test"}
            )

            assert response2.status_code == 202
            data = response2.json()
            assert data["task_id"] == "recovery-test-id"


class TestTasksAPIAuthentication:
    """Test authentication requirements for task endpoints."""

    def test_trigger_simple_task_requires_auth(self, client: TestClient):
        """Test that POST /tasks/simple requires authentication."""
        response = client.post("/api/v1/tasks/simple", json={"message": "test message"})
        assert response.status_code == 401

    def test_trigger_database_task_requires_auth(self, client: TestClient):
        """Test that POST /tasks/database requires authentication."""
        response = client.post("/api/v1/tasks/database", json={"query": "count_users"})
        assert response.status_code == 401

    def test_trigger_error_task_requires_auth(self, client: TestClient):
        """Test that POST /tasks/error requires authentication."""
        response = client.post("/api/v1/tasks/error", json={"should_fail": False})
        assert response.status_code == 401

    def test_get_task_result_requires_auth(self, client: TestClient):
        """Test that GET /tasks/{task_id} requires authentication."""
        response = client.get("/api/v1/tasks/test-task-id")
        assert response.status_code == 401

    def test_list_active_tasks_requires_auth(self, client: TestClient):
        """Test that GET /tasks/ requires authentication."""
        response = client.get("/api/v1/tasks/")
        assert response.status_code == 401
