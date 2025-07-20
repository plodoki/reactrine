"""
Tests for the main application endpoints.

This module contains tests for the core application endpoints including
the health check and any root-level endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """
    Test the health check endpoint.

    The health check should return a 200 status code and include
    status information about the application and database.
    """
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "details" in data
    assert "version" in data

    # Check that details include expected components
    details = data["details"]
    assert "database" in details
    assert "api" in details

    # API should always be running in tests
    assert details["api"] == "running"


def test_health_check_structure(client: TestClient):
    """
    Test that the health check response has the expected structure.
    """
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    # Verify the response structure
    required_fields = ["status", "details", "version"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Verify details structure
    details = data["details"]
    required_detail_fields = ["database", "api"]
    for field in required_detail_fields:
        assert field in details, f"Missing required detail field: {field}"


def test_health_check_content_type(client: TestClient):
    """
    Test that the health check returns JSON content type.
    """
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


@pytest.mark.asyncio
async def test_health_check_async(async_client):
    """
    Test the health check endpoint using async client.
    """
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "details" in data


def test_nonexistent_endpoint(client: TestClient):
    """
    Test that accessing a non-existent endpoint returns 404.
    """
    response = client.get("/api/v1/nonexistent")

    assert response.status_code == 404


def test_api_versioning(client: TestClient):
    """
    Test that the API is properly versioned under /api/v1.
    """
    # Health check should be available under versioned path
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    # Health check should not be available at root
    response = client.get("/health")
    assert response.status_code == 404


def test_generate_haiku(client: TestClient, monkeypatch):
    """Test the haiku generation endpoint."""

    from app.schemas.haiku import HaikuResponse
    from app.services.haiku import HaikuService

    mock_response = HaikuResponse(
        haiku="line1\nline2\nline3",
        lines=["line1", "line2", "line3"],
        syllables=[5, 7, 5],
        model_used="test-model",
        provider_used="openai",
    )

    async def mock_generate_haiku(self, request):
        return mock_response

    monkeypatch.setattr(HaikuService, "generate_haiku", mock_generate_haiku)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    payload = {"topic": "nature", "style": "traditional"}
    response = client.post("/api/v1/haiku", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "haiku": "line1\nline2\nline3",
        "lines": ["line1", "line2", "line3"],
        "syllables": [5, 7, 5],
        "model_used": "test-model",
        "provider_used": "openai",
    }
