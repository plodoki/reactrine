"""Unit tests for OAuth service."""

import time
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import HTTPException, status

from app.services.oauth import GoogleUserInfo, OAuthService


class TestOAuthService:
    """Test suite for OAuth service."""

    @pytest.fixture
    def oauth_service(self):
        """Create OAuth service instance for testing."""
        return OAuthService(timeout=5)

    @pytest.fixture
    def valid_google_token_data(self):
        """Valid Google token response data."""
        return {
            "aud": "test-client-id",
            "exp": str(int(time.time()) + 3600),  # Expires in 1 hour
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
        }

    @pytest.fixture
    def expired_google_token_data(self):
        """Expired Google token response data."""
        return {
            "aud": "test-client-id",
            "exp": str(int(time.time()) - 3600),  # Expired 1 hour ago
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
        }

    @pytest.fixture
    def invalid_audience_token_data(self):
        """Google token with invalid audience."""
        return {
            "aud": "wrong-client-id",
            "exp": str(int(time.time()) + 3600),
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
        }

    @pytest.fixture
    def unverified_email_token_data(self):
        """Google token with unverified email."""
        return {
            "aud": "test-client-id",
            "exp": str(int(time.time()) + 3600),
            "email": "test@example.com",
            "email_verified": False,
            "name": "Test User",
        }

    @pytest.mark.asyncio
    async def test_verify_google_token_success(
        self, oauth_service, valid_google_token_data, monkeypatch
    ):
        """Test successful Google token verification."""
        # Mock httpx client
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value=valid_google_token_data)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        async def mock_client_context(*args, **kwargs):
            return mock_client

        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: mock_client)

        # Test token verification
        result = await oauth_service.verify_google_token(
            token="valid-token", client_id="test-client-id"
        )

        # Verify result
        assert isinstance(result, GoogleUserInfo)
        assert result.email == "test@example.com"
        assert result.email_verified is True
        assert result.name == "Test User"
        assert result.picture == "https://example.com/avatar.jpg"

        # Verify client was called correctly
        mock_client.post.assert_called_once_with(
            "https://oauth2.googleapis.com/tokeninfo", data={"id_token": "valid-token"}
        )

    @pytest.mark.asyncio
    async def test_verify_google_token_expired(
        self, oauth_service, expired_google_token_data, monkeypatch
    ):
        """Test Google token verification with expired token."""
        # Mock httpx client
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value=expired_google_token_data)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: mock_client)

        # Test token verification should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_google_token(
                token="expired-token", client_id="test-client-id"
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_verify_google_token_invalid_audience(
        self, oauth_service, invalid_audience_token_data, monkeypatch
    ):
        """Test Google token verification with invalid audience."""
        # Mock httpx client
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value=invalid_audience_token_data)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: mock_client)

        # Test token verification should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_google_token(
                token="invalid-audience-token", client_id="test-client-id"
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "audience" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_verify_google_token_unverified_email(
        self, oauth_service, unverified_email_token_data, monkeypatch
    ):
        """Test Google token verification with unverified email."""
        # Mock httpx client
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value=unverified_email_token_data)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: mock_client)

        # Test token verification should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_google_token(
                token="unverified-email-token", client_id="test-client-id"
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "unverified" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_verify_google_token_network_error(self, oauth_service, monkeypatch):
        """Test Google token verification with network error."""
        # Mock httpx client to raise network error
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.RequestError("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: mock_client)

        # Test token verification should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_google_token(
                token="network-error-token", client_id="test-client-id"
            )

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "network error" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_verify_google_token_http_error(self, oauth_service, monkeypatch):
        """Test Google token verification with HTTP error."""
        # Mock httpx client to raise HTTP error
        mock_response = Mock()
        mock_response.status_code = 400

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Bad request", request=Mock(), response=mock_response
            )
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: mock_client)

        # Test token verification should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_google_token(
                token="http-error-token", client_id="test-client-id"
            )

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "service error" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_verify_google_token_missing_email(self, oauth_service, monkeypatch):
        """Test Google token verification with missing email."""
        token_data = {
            "aud": "test-client-id",
            "exp": str(int(time.time()) + 3600),
            "email_verified": True,
            "name": "Test User",
            # Missing email field
        }

        # Mock httpx client
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value=token_data)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: mock_client)

        # Test token verification should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_google_token(
                token="missing-email-token", client_id="test-client-id"
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_verify_google_token_unexpected_error(
        self, oauth_service, monkeypatch
    ):
        """Test Google token verification with unexpected error."""
        # Mock httpx client to raise unexpected error
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=RuntimeError("Unexpected error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: mock_client)

        # Test token verification should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_google_token(
                token="unexpected-error-token", client_id="test-client-id"
            )

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "failed" in exc_info.value.detail.lower()

    def test_oauth_service_initialization(self):
        """Test OAuth service initialization with custom timeout."""
        service = OAuthService(timeout=30)
        assert service.timeout == 30

    def test_oauth_service_default_timeout(self):
        """Test OAuth service initialization with default timeout."""
        service = OAuthService()
        assert service.timeout == 10


class TestGoogleUserInfo:
    """Test suite for GoogleUserInfo model."""

    def test_google_user_info_creation(self):
        """Test GoogleUserInfo model creation with all fields."""
        user_info = GoogleUserInfo(
            email="test@example.com",
            email_verified=True,
            name="Test User",
            picture="https://example.com/avatar.jpg",
        )

        assert user_info.email == "test@example.com"
        assert user_info.email_verified is True
        assert user_info.name == "Test User"
        assert user_info.picture == "https://example.com/avatar.jpg"

    def test_google_user_info_optional_fields(self):
        """Test GoogleUserInfo model creation with optional fields."""
        user_info = GoogleUserInfo(email="test@example.com", email_verified=True)

        assert user_info.email == "test@example.com"
        assert user_info.email_verified is True
        assert user_info.name is None
        assert user_info.picture is None
