"""
Tests for API keys endpoints.

These tests verify the API key management endpoints work correctly.
"""

import os
from unittest.mock import patch

from fastapi import status

from app.utils.rsa_keys import clear_key_cache


class TestApiKeysEndpoints:
    """Test API keys REST endpoints."""

    def setup_method(self):
        """Clear key cache before each test."""
        clear_key_cache()

    def teardown_method(self):
        """Clear key cache after each test."""
        clear_key_cache()

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_api_keys_endpoints_import(self):
        """Test that API keys endpoints can be imported without errors."""
        # This is a basic smoke test to ensure our modules import correctly
        from app.api.v1.endpoints.api_keys import router
        from app.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyList
        from app.services.api_key import create_api_key_simple

        # Verify basic objects exist
        assert router is not None
        assert ApiKeyCreate is not None
        assert ApiKeyList is not None
        assert ApiKeyCreated is not None
        assert create_api_key_simple is not None

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_api_key_schema_validation(self):
        """Test API key schema validation."""
        from app.schemas.api_key import ApiKeyCreate

        # Test valid data
        valid_data = ApiKeyCreate(label="Test Key", expires_in_days=30)
        assert valid_data.label == "Test Key"
        assert valid_data.expires_in_days == 30

        # Test default values
        default_data = ApiKeyCreate()
        assert default_data.expires_in_days == 30

        # Test validation - should work for valid ranges
        valid_range = ApiKeyCreate(expires_in_days=1)
        assert valid_range.expires_in_days == 1

        valid_range_max = ApiKeyCreate(expires_in_days=90)
        assert valid_range_max.expires_in_days == 90

        # Test that None is allowed (no expiry)
        no_expiry = ApiKeyCreate(expires_in_days=None)
        assert no_expiry.expires_in_days is None

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_create_api_key_success(self, authenticated_client):
        """Test successful API key creation."""
        payload = {"label": "Test API Key", "expires_in_days": 30}

        response = authenticated_client.post("/api/v1/users/me/api-keys/", json=payload)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert "api_key" in data
        assert "token" in data
        assert data["api_key"]["label"] == "Test API Key"
        assert data["api_key"]["id"] is not None
        assert data["api_key"]["is_active"] is True
        assert data["api_key"]["expires_at"] is not None
        assert data["api_key"]["created_at"] is not None

        # Verify token format
        token = data["token"]
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT format

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_create_api_key_invalid_data(self, authenticated_client):
        """Test API key creation with invalid data."""
        payload = {"label": "", "expires_in_days": 400}  # Invalid label and expiry

        response = authenticated_client.post("/api/v1/users/me/api-keys/", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_list_api_keys(self, authenticated_client):
        """Test listing API keys."""
        response = authenticated_client.get("/api/v1/users/me/api-keys/")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, dict)
        assert "keys" in data
        assert "total" in data
        assert isinstance(data["keys"], list)
        assert isinstance(data["total"], int)

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_revoke_api_key(self, authenticated_client):
        """Test revoking an API key."""
        # First create an API key
        create_payload = {"label": "Test Key for Revocation", "expires_in_days": 30}
        create_response = authenticated_client.post(
            "/api/v1/users/me/api-keys/", json=create_payload
        )

        assert create_response.status_code == status.HTTP_200_OK
        api_key_id = create_response.json()["api_key"]["id"]

        # Then revoke it (note: URL should not have trailing slash)
        revoke_response = authenticated_client.delete(
            f"/api/v1/users/me/api-keys/{api_key_id}"
        )

        assert revoke_response.status_code == status.HTTP_200_OK

        revoked_data = revoke_response.json()
        # Check for the fields that are actually returned
        assert revoked_data["success"] is True
        assert "message" in revoked_data
