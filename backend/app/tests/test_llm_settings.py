class TestLLMSettings:
    """Test cases for LLM settings endpoints."""

    def test_get_llm_settings_without_auth(self, client):
        """Test that GET /llm-settings requires authentication."""
        response = client.get("/api/v1/llm-settings")
        assert response.status_code == 401
        error_data = response.json()
        assert "detail" in error_data
        assert "Authentication required" in error_data["detail"]

    def test_create_llm_settings_without_auth(self, client):
        """Test that POST /llm-settings requires authentication."""
        payload = {
            "provider": "openai",
            "openai_model": "gpt-4o-mini",
            "openrouter_model": "google/gemini-2.5-flash",
            "bedrock_model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        }
        response = client.post("/api/v1/llm-settings", json=payload)
        assert response.status_code == 401

    def test_update_llm_settings_without_auth(self, client):
        """Test that PATCH /llm-settings requires authentication."""
        payload = {"provider": "bedrock"}
        response = client.patch("/api/v1/llm-settings", json=payload)
        assert response.status_code == 401

    def test_get_llm_settings_requires_admin(self, authenticated_client):
        """Test that GET /llm-settings requires admin role."""
        response = authenticated_client.get("/api/v1/llm-settings")
        assert response.status_code == 403
        error_data = response.json()
        assert "detail" in error_data
        assert "Insufficient permissions" in error_data["detail"]

    def test_get_llm_settings_not_found(self, admin_authenticated_client):
        """Test GET /llm-settings when no settings exist."""
        response = admin_authenticated_client.get("/api/v1/llm-settings")
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
        assert "LLM settings not found" in error_data["detail"]

    def test_create_llm_settings_success(self, admin_authenticated_client):
        """Test successful creation of LLM settings."""
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

    def test_create_llm_settings_already_exists(self, admin_authenticated_client):
        """Test creating LLM settings when they already exist."""
        # First, create settings
        payload = {
            "provider": "openai",
            "openai_model": "gpt-4o-mini",
            "openrouter_model": "google/gemini-2.5-flash",
            "bedrock_model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        }
        response = admin_authenticated_client.post("/api/v1/llm-settings", json=payload)
        assert response.status_code == 200

        # Try to create again - should conflict
        response = admin_authenticated_client.post("/api/v1/llm-settings", json=payload)
        assert response.status_code == 409
        error_data = response.json()
        assert "detail" in error_data
        assert "already exist" in error_data["detail"]

    def test_get_llm_settings_success(self, admin_authenticated_client):
        """Test successful retrieval of existing LLM settings."""
        # First, create settings
        payload = {
            "provider": "openai",
            "openai_model": "gpt-4o-mini",
            "openrouter_model": "google/gemini-2.5-flash",
            "bedrock_model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        }
        create_response = admin_authenticated_client.post(
            "/api/v1/llm-settings", json=payload
        )
        assert create_response.status_code == 200

        # Then get the settings
        response = admin_authenticated_client.get("/api/v1/llm-settings")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "openai"
        assert data["openai_model"] == "gpt-4o-mini"

    def test_update_llm_settings_not_found(self, admin_authenticated_client):
        """Test PATCH /llm-settings when no settings exist."""
        payload = {"provider": "bedrock"}
        response = admin_authenticated_client.patch(
            "/api/v1/llm-settings", json=payload
        )
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
        assert "LLM settings not found" in error_data["detail"]

    def test_update_llm_settings_success(self, admin_authenticated_client):
        """Test successful update of LLM settings."""
        # First, create settings
        create_payload = {
            "provider": "openai",
            "openai_model": "gpt-4o-mini",
            "openrouter_model": "google/gemini-2.5-flash",
            "bedrock_model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        }
        create_response = admin_authenticated_client.post(
            "/api/v1/llm-settings", json=create_payload
        )
        assert create_response.status_code == 200

        # Then update the settings
        update_payload = {
            "provider": "bedrock",
            "bedrock_model": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
        }
        response = admin_authenticated_client.patch(
            "/api/v1/llm-settings", json=update_payload
        )
        assert response.status_code == 200

        data = response.json()
        assert data["provider"] == "bedrock"
        assert data["bedrock_model"] == "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        # Ensure other fields are preserved
        assert data["openai_model"] == "gpt-4o-mini"

    def test_update_llm_settings_partial(self, admin_authenticated_client):
        """Test partial update of LLM settings."""
        # First, create settings
        create_payload = {
            "provider": "openai",
            "openai_model": "gpt-4o-mini",
            "openrouter_model": "google/gemini-2.5-flash",
            "bedrock_model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        }
        create_response = admin_authenticated_client.post(
            "/api/v1/llm-settings", json=create_payload
        )
        assert create_response.status_code == 200

        # Update only the model, keep same provider
        update_payload = {"openai_model": "gpt-4o"}
        response = admin_authenticated_client.patch(
            "/api/v1/llm-settings", json=update_payload
        )
        assert response.status_code == 200

        data = response.json()
        assert data["provider"] == "openai"  # Unchanged
        assert data["openai_model"] == "gpt-4o"  # Updated
        assert data["openrouter_model"] == "google/gemini-2.5-flash"  # Unchanged
