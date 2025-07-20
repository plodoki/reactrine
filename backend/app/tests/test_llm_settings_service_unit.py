"""
Unit tests for the LLM settings service.

Tests the LLM settings service with various scenarios including
creation, retrieval, updates, and error handling.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.models.llm_settings import LLMSettings
from app.schemas.llm_settings import (
    LLMSettingsCreateSchema,
    LLMSettingsSchema,
    LLMSettingsUpdateSchema,
)
from app.services.llm_settings import LLMSettingsService


class TestLLMSettingsService:
    """Test suite for LLM settings service."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        mock_settings = Mock()
        mock_settings.DEFAULT_LLM_MODEL = "gpt-4o-mini"
        mock_settings.OPENROUTER_MODEL = "openrouter/auto"
        mock_settings.BEDROCK_MODEL = "anthropic.claude-3-sonnet"
        mock_settings.LMSTUDIO_MODEL = "llama-3.1-8b"
        mock_settings.LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
        return mock_settings

    @pytest.fixture
    def llm_service(self, mock_settings):
        """Create LLM settings service instance for testing."""
        return LLMSettingsService(settings=mock_settings)

    @pytest_asyncio.fixture
    async def mock_db_session(self):
        """Create mock database session using new mock utilities."""
        from app.tests.mocks import create_mock_db_session

        async for db in create_mock_db_session():
            yield db

    @pytest.fixture
    def sample_llm_settings(self):
        """Sample LLM settings for testing."""
        return LLMSettings(
            id=1,
            provider="openai",
            openai_model="gpt-4o-mini",
            openrouter_model="openrouter/auto",
            bedrock_model="anthropic.claude-3-sonnet",
            lmstudio_model="llama-3.1-8b",
        )

    @pytest.mark.asyncio
    async def test_get_settings_success(
        self, llm_service, mock_db_session, sample_llm_settings
    ):
        """Test successful retrieval of LLM settings."""
        mock_db_session.get = AsyncMock(return_value=sample_llm_settings)

        result = await llm_service.get_settings(mock_db_session)

        assert isinstance(result, LLMSettingsSchema)
        assert result.id == 1
        assert result.provider == "openai"
        assert result.openai_model == "gpt-4o-mini"
        mock_db_session.get.assert_called_once_with(LLMSettings, 1)

    @pytest.mark.asyncio
    async def test_get_settings_not_found(self, llm_service, mock_db_session):
        """Test retrieval when settings don't exist."""
        mock_db_session.get = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await llm_service.get_settings(mock_db_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_settings_database_error(self, llm_service, mock_db_session):
        """Test retrieval with database error."""
        mock_db_session.get = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        with pytest.raises(HTTPException) as exc_info:
            await llm_service.get_settings(mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_settings_success(self, llm_service, mock_db_session):
        """Test successful creation of LLM settings."""
        # Mock no existing settings
        mock_db_session.get = AsyncMock(return_value=None)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Test data
        payload = LLMSettingsCreateSchema(
            provider="openai",
            openai_model="gpt-4o-mini",
            openrouter_model=None,
            bedrock_model=None,
            lmstudio_model=None,
        )

        # Mock refresh to populate the created settings
        def mock_refresh(settings):
            settings.id = 1

        mock_db_session.refresh.side_effect = mock_refresh

        result = await llm_service.create_llm_settings(payload, mock_db_session)

        assert isinstance(result, LLMSettingsSchema)
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_settings_already_exist(
        self, llm_service, mock_db_session, sample_llm_settings
    ):
        """Test creation when settings already exist (race condition)."""
        from sqlalchemy.exc import IntegrityError

        # Mock database session to simulate IntegrityError on commit
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock(
            side_effect=IntegrityError(
                "duplicate key value violates unique constraint", None, None
            )
        )
        mock_db_session.rollback = AsyncMock()

        payload = LLMSettingsCreateSchema(provider="openai", openai_model="gpt-4o-mini")

        with pytest.raises(HTTPException) as exc_info:
            await llm_service.create_llm_settings(payload, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already exist" in exc_info.value.detail
        # Rollback is called twice: once in repository, once in service
        assert mock_db_session.rollback.call_count == 2

    @pytest.mark.asyncio
    async def test_create_settings_database_error(self, llm_service, mock_db_session):
        """Test creation with database error."""
        mock_db_session.get = AsyncMock(return_value=None)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock(
            side_effect=SQLAlchemyError("Database error")
        )
        mock_db_session.rollback = AsyncMock()

        payload = LLMSettingsCreateSchema(provider="openai", openai_model="gpt-4o-mini")

        with pytest.raises(HTTPException) as exc_info:
            await llm_service.create_llm_settings(payload, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to create" in exc_info.value.detail
        # Rollback is called twice: once in repository, once in service
        assert mock_db_session.rollback.call_count == 2

    @pytest.mark.asyncio
    async def test_update_settings_success(
        self, llm_service, mock_db_session, sample_llm_settings
    ):
        """Test successful update of LLM settings."""
        mock_db_session.get = AsyncMock(return_value=sample_llm_settings)
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Test update payload
        payload = LLMSettingsUpdateSchema(
            provider="bedrock",
            bedrock_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        )

        result = await llm_service.update_llm_settings(payload, mock_db_session)

        assert isinstance(result, LLMSettingsSchema)
        assert sample_llm_settings.provider == "bedrock"
        assert (
            sample_llm_settings.bedrock_model
            == "anthropic.claude-3-5-sonnet-20241022-v2:0"
        )
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_settings_not_found(self, llm_service, mock_db_session):
        """Test update when settings don't exist."""
        mock_db_session.get = AsyncMock(return_value=None)

        payload = LLMSettingsUpdateSchema(provider="openai")

        with pytest.raises(HTTPException) as exc_info:
            await llm_service.update_llm_settings(payload, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_settings_provider_model_validation_error(
        self, llm_service, mock_db_session, sample_llm_settings
    ):
        """Test update with provider/model validation error when no default available."""
        # Set up existing settings with empty model for new provider
        sample_llm_settings.bedrock_model = ""
        mock_db_session.get = AsyncMock(return_value=sample_llm_settings)

        # Mock the service with no default model for bedrock to trigger validation error
        llm_service._provider_model_mapping["bedrock"] = ("bedrock_model", "")

        payload = LLMSettingsUpdateSchema(provider="bedrock")

        with pytest.raises(HTTPException) as exc_info:
            await llm_service.update_llm_settings(payload, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Bedrock model must be provided" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_settings_database_error(
        self, llm_service, mock_db_session, sample_llm_settings
    ):
        """Test update with database error."""
        mock_db_session.get = AsyncMock(return_value=sample_llm_settings)
        mock_db_session.commit = AsyncMock(
            side_effect=SQLAlchemyError("Database error")
        )
        mock_db_session.rollback = AsyncMock()

        payload = LLMSettingsUpdateSchema(provider="openai")

        with pytest.raises(HTTPException) as exc_info:
            await llm_service.update_llm_settings(payload, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to update" in exc_info.value.detail
        # Rollback is called twice: once in repository, once in service
        assert mock_db_session.rollback.call_count == 2

    def test_apply_provider_auto_population_no_existing_model(
        self, llm_service, sample_llm_settings
    ):
        """Test auto-population when no existing model for new provider."""
        sample_llm_settings.openrouter_model = ""
        update_data = {"provider": "openrouter"}

        result = llm_service._apply_provider_auto_population(
            update_data, sample_llm_settings
        )

        # Should auto-populate with default model
        assert result == {
            "provider": "openrouter",
            "openrouter_model": "openrouter/auto",
        }

    def test_apply_provider_auto_population_existing_model(
        self, llm_service, sample_llm_settings
    ):
        """Test auto-population retains existing valid model."""
        sample_llm_settings.openrouter_model = "existing-model"
        update_data = {"provider": "openrouter"}

        result = llm_service._apply_provider_auto_population(
            update_data, sample_llm_settings
        )

        # Should retain existing model
        assert result == {"provider": "openrouter"}

    def test_apply_provider_auto_population_with_explicit_model(
        self, llm_service, sample_llm_settings
    ):
        """Test auto-population when model explicitly provided in update."""
        update_data = {"provider": "openrouter", "openrouter_model": "new-model"}

        result = llm_service._apply_provider_auto_population(
            update_data, sample_llm_settings
        )

        # Should not change anything when model explicitly provided
        assert result == {"provider": "openrouter", "openrouter_model": "new-model"}

    def test_validate_provider_model_combination_success(
        self, llm_service, sample_llm_settings
    ):
        """Test successful provider/model combination validation."""
        update_data = {"provider": "openai", "openai_model": "gpt-4"}

        # Should not raise any exception
        llm_service._validate_provider_model_combination(
            update_data, sample_llm_settings
        )

    def test_validate_provider_model_combination_existing_model(
        self, llm_service, sample_llm_settings
    ):
        """Test validation using existing model."""
        sample_llm_settings.openai_model = "existing-model"
        update_data = {"provider": "openai"}

        # Should not raise any exception since existing model is valid
        llm_service._validate_provider_model_combination(
            update_data, sample_llm_settings
        )

    def test_validate_provider_model_combination_missing_model(
        self, llm_service, sample_llm_settings
    ):
        """Test validation error when model is missing."""
        sample_llm_settings.lmstudio_model = ""
        update_data = {"provider": "lmstudio"}

        with pytest.raises(HTTPException) as exc_info:
            llm_service._validate_provider_model_combination(
                update_data, sample_llm_settings
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "LMStudio model must be provided" in exc_info.value.detail

    def test_validate_provider_model_combination_no_provider_update(
        self, llm_service, sample_llm_settings
    ):
        """Test validation skipped when no provider update."""
        update_data = {"openai_model": "new-model"}

        # Should not raise any exception when provider is not being updated
        llm_service._validate_provider_model_combination(
            update_data, sample_llm_settings
        )

    @pytest.mark.asyncio
    async def test_get_lmstudio_models_success(self, llm_service, mock_settings):
        """Test successful LMStudio models retrieval."""
        mock_models = ["model1", "model2", "model3"]

        with patch(
            "app.services.llm_settings.LMStudioLLMProvider"
        ) as mock_provider_class:
            mock_provider = Mock()
            mock_provider.get_available_models = AsyncMock(return_value=mock_models)
            mock_provider_class.return_value = mock_provider

            result = await llm_service.get_lmstudio_models()

            assert result == mock_models
            mock_provider.get_available_models.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_lmstudio_models_empty_result(self, llm_service, mock_settings):
        """Test LMStudio models retrieval with empty result."""
        with patch(
            "app.services.llm_settings.LMStudioLLMProvider"
        ) as mock_provider_class:
            mock_provider = Mock()
            mock_provider.get_available_models = AsyncMock(return_value=[])
            mock_provider_class.return_value = mock_provider

            result = await llm_service.get_lmstudio_models()

            assert result == []

    @pytest.mark.asyncio
    async def test_get_lmstudio_models_error(self, llm_service, mock_settings):
        """Test LMStudio models retrieval with error."""
        with patch(
            "app.services.llm_settings.LMStudioLLMProvider"
        ) as mock_provider_class:
            mock_provider = Mock()
            mock_provider.get_available_models = AsyncMock(
                side_effect=Exception("Connection error")
            )
            mock_provider_class.return_value = mock_provider

            with pytest.raises(HTTPException) as exc_info:
                await llm_service.get_lmstudio_models()

            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "Unable to fetch models" in exc_info.value.detail

    def test_provider_model_mapping_initialization(self, llm_service, mock_settings):
        """Test that provider model mapping is properly initialized."""
        expected_mapping = {
            "openai": ("openai_model", mock_settings.DEFAULT_LLM_MODEL),
            "openrouter": ("openrouter_model", mock_settings.OPENROUTER_MODEL),
            "bedrock": ("bedrock_model", mock_settings.BEDROCK_MODEL),
            "lmstudio": ("lmstudio_model", mock_settings.LMSTUDIO_MODEL),
        }

        assert llm_service._provider_model_mapping == expected_mapping

    def test_service_initialization_with_default_settings(self):
        """Test service initialization with default settings."""
        with patch("app.services.llm_settings.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_get_settings.return_value = mock_settings

            service = LLMSettingsService()

            assert service.settings == mock_settings
            mock_get_settings.assert_called_once()

    def test_service_initialization_with_custom_settings(self, mock_settings):
        """Test service initialization with custom settings."""
        service = LLMSettingsService(settings=mock_settings)

        assert service.settings == mock_settings


class TestLLMSettingsServiceIntegration:
    """Integration tests for LLM settings service."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for integration tests."""
        mock_settings = Mock()
        mock_settings.DEFAULT_LLM_MODEL = "gpt-4o-mini"
        mock_settings.OPENROUTER_MODEL = "openrouter/auto"
        mock_settings.BEDROCK_MODEL = "anthropic.claude-3-sonnet"
        mock_settings.LMSTUDIO_MODEL = "llama-3.1-8b"
        mock_settings.LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
        return mock_settings

    @pytest.mark.asyncio
    async def test_full_create_update_cycle(self, mock_settings):
        """Test complete create and update cycle."""
        from app.tests.mocks import create_mock_db_session

        service = LLMSettingsService(settings=mock_settings)

        async for mock_db in create_mock_db_session():
            # Mock database operations for create
            mock_db.get = AsyncMock(return_value=None)  # No existing settings
            mock_db.add = Mock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            # Create settings
            create_payload = LLMSettingsCreateSchema(
                provider="openai",
                openai_model="gpt-4o-mini",
            )

            # Mock refresh to simulate database behavior
            def mock_refresh(settings):
                settings.id = 1

            mock_db.refresh.side_effect = mock_refresh

            created = await service.create_llm_settings(create_payload, mock_db)
            assert created.provider == "openai"

            # Mock database operations for update
            mock_settings_obj = LLMSettings(
                id=1,
                provider="openai",
                openai_model="gpt-4o-mini",
                openrouter_model="openrouter/auto",
                bedrock_model="anthropic.claude-3-sonnet",
                lmstudio_model="llama-3.1-8b",
            )
            mock_db.get = AsyncMock(return_value=mock_settings_obj)

            # Update settings
            update_payload = LLMSettingsUpdateSchema(
                provider="bedrock",
                bedrock_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            )

            updated = await service.update_llm_settings(update_payload, mock_db)
            assert updated.provider == "bedrock"
