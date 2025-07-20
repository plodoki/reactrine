"""
Unit tests for API error handling utilities.

These tests verify that the error handling utilities properly create
HTTPExceptions with the correct status codes and details.
"""

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.utils import handle_database_error_legacy, handle_llm_error
from app.services.llm.exceptions import LLMConfigurationError, LLMGenerationError
from app.utils.error_handling import (
    raise_bad_request_error,
    raise_conflict_error,
    raise_internal_server_error,
    raise_not_found_error,
    raise_service_unavailable_error,
)


class TestErrorUtilities:
    """Test error utility functions."""

    def test_raise_not_found_error_default_message(self):
        """Test raising 404 error with default message."""
        with pytest.raises(HTTPException) as exc_info:
            raise_not_found_error("User")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"

    def test_raise_not_found_error_custom_message(self):
        """Test raising 404 error with custom message."""
        with pytest.raises(HTTPException) as exc_info:
            raise_not_found_error("User", "Custom not found message")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Custom not found message"

    def test_raise_conflict_error_default_message(self):
        """Test raising 409 error with default message."""
        with pytest.raises(HTTPException) as exc_info:
            raise_conflict_error("User")

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert exc_info.value.detail == "User already exists"

    def test_raise_conflict_error_custom_message(self):
        """Test raising 409 error with custom message."""
        with pytest.raises(HTTPException) as exc_info:
            raise_conflict_error("User", "Custom conflict message")

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert exc_info.value.detail == "Custom conflict message"

    def test_raise_bad_request_error(self):
        """Test raising 400 error."""
        with pytest.raises(HTTPException) as exc_info:
            raise_bad_request_error("Invalid input")

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Invalid input"

    def test_raise_service_unavailable_error_default_message(self):
        """Test raising 503 error with default message."""
        with pytest.raises(HTTPException) as exc_info:
            raise_service_unavailable_error()

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert exc_info.value.detail == "Service is currently unavailable"

    def test_raise_service_unavailable_error_custom_message(self):
        """Test raising 503 error with custom message."""
        with pytest.raises(HTTPException) as exc_info:
            raise_service_unavailable_error("Custom service error")

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert exc_info.value.detail == "Custom service error"

    def test_raise_internal_server_error_default_message(self):
        """Test raising 500 error with default message."""
        with pytest.raises(HTTPException) as exc_info:
            raise_internal_server_error()

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Internal server error"

    def test_raise_internal_server_error_custom_message(self):
        """Test raising 500 error with custom message."""
        with pytest.raises(HTTPException) as exc_info:
            raise_internal_server_error("Custom server error")

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Custom server error"


class TestDatabaseErrorHandling:
    """Test database error handling utilities."""

    @pytest.mark.asyncio
    async def test_handle_database_error_with_rollback(self):
        """Test handling database error with rollback."""
        from app.tests.mocks import create_mock_db_session

        mock_error = SQLAlchemyError("Test error")

        async for mock_db in create_mock_db_session():
            with pytest.raises(HTTPException) as exc_info:
                await handle_database_error_legacy(
                    mock_db, "test operation", mock_error
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert exc_info.value.detail == "Database operation failed"
            mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_database_error_without_rollback(self):
        """Test handling database error without rollback."""
        from app.tests.mocks import create_mock_db_session

        mock_error = SQLAlchemyError("Test error")

        async for mock_db in create_mock_db_session():
            with pytest.raises(HTTPException) as exc_info:
                await handle_database_error_legacy(
                    mock_db, "test operation", mock_error, rollback=False
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert exc_info.value.detail == "Database operation failed"
            mock_db.rollback.assert_not_called()


class TestLLMErrorHandling:
    """Test LLM error handling utilities."""

    def test_handle_llm_configuration_error(self):
        """Test handling LLM configuration error."""
        error = LLMConfigurationError("Config error")

        with pytest.raises(HTTPException) as exc_info:
            handle_llm_error(error, "test operation")

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "LLM service is not configured properly"

    def test_handle_llm_generation_error(self):
        """Test handling LLM generation error."""
        error = LLMGenerationError("Generation failed")

        with pytest.raises(HTTPException) as exc_info:
            handle_llm_error(error, "test operation")

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "AI service is currently unavailable" in exc_info.value.detail

    def test_handle_unexpected_error(self):
        """Test handling unexpected error."""
        error = ValueError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            handle_llm_error(error, "test operation")

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Invalid input value"
