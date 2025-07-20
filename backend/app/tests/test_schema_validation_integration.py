"""Integration tests to verify Pydantic validation works with API endpoints."""


class TestLLMSettingsValidationIntegration:
    """Test LLM settings validation in API endpoints."""

    def test_create_settings_validation_in_api(self, admin_authenticated_client):
        """Test that API validation catches invalid provider."""
        payload = {"provider": ""}  # Empty provider should fail validation
        response = admin_authenticated_client.post("/api/v1/llm-settings", json=payload)

        assert response.status_code == 422
        data = response.json()
        # Check the validation error structure - should be in 'errors' field
        assert "errors" in data
        errors = data["errors"]
        assert any("provider" in str(error).lower() for error in errors)

    def test_create_settings_with_whitespace_model(self, admin_authenticated_client):
        """Test that API correctly trims whitespace in model fields."""
        payload = {
            "provider": "openai",
            "openai_model": "  gpt-4o-mini  ",  # Should be trimmed
        }
        response = admin_authenticated_client.post("/api/v1/llm-settings", json=payload)

        # Should succeed after trimming whitespace
        assert response.status_code == 200
        data = response.json()
        assert data["openai_model"] == "gpt-4o-mini"  # Should be trimmed

    def test_create_settings_success_after_validation(self, admin_authenticated_client):
        """Test successful creation after validation passes."""
        # Valid payload that should pass all validation
        payload = {
            "provider": "openai",
            "openai_model": "gpt-4o-mini",
            "openrouter_model": "google/gemini-2.5-flash",
            "bedrock_model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        }

        response = admin_authenticated_client.post("/api/v1/llm-settings", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["provider"] == "openai"
        assert data["openai_model"] == "gpt-4o-mini"
        assert data["openrouter_model"] == "google/gemini-2.5-flash"
        assert data["bedrock_model"] == "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

    def test_update_settings_validation_with_existing_data(
        self, admin_authenticated_client
    ):
        """Test validation with existing data and updates."""
        # First create settings
        create_payload = {
            "provider": "openai",
            "openai_model": "gpt-4o-mini",
            "openrouter_model": "google/gemini-2.5-flash",
            "bedrock_model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        }
        response = admin_authenticated_client.post(
            "/api/v1/llm-settings", json=create_payload
        )
        assert response.status_code == 200  # Should succeed with auto-population

        # Now try to update with partial data
        update_payload = {
            "openai_model": "   gpt-4-turbo   ",  # Should trim whitespace
        }
        response = admin_authenticated_client.patch(
            "/api/v1/llm-settings", json=update_payload
        )
        assert response.status_code == 200  # Should succeed

        # Verify the model was trimmed
        data = response.json()
        assert data["openai_model"] == "gpt-4-turbo"  # Should be trimmed
