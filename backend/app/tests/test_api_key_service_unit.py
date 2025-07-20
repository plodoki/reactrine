"""
Unit tests for the API key service.

Tests the updated API key service with RSA-based token creation.
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.api_key import ApiKey
from app.models.user import User
from app.services.api_key import (
    create_api_key_simple,
    get_api_key_by_id,
    get_api_key_by_jti,
    revoke_api_key_simple,
    update_api_key_last_used,
    verify_api_key_by_hash,
)
from app.tests.mocks import create_mock_db_session
from app.utils.rsa_keys import clear_key_cache


class TestApiKeyService:
    """Test API key service functions."""

    def setup_method(self):
        """Clear key cache before each test."""
        clear_key_cache()

    def teardown_method(self):
        """Clear key cache after each test."""
        clear_key_cache()

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_create_api_key_simple_success(self):
        """Test successful API key creation."""
        # Create test user
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Create API key
            api_key, token = await create_api_key_simple(
                db=db_mock, user=user, label="Test Key", expires_in_days=30
            )

            # Verify API key object
            assert isinstance(api_key, ApiKey)
            assert api_key.user_id == user.id
            assert api_key.label == "Test Key"
            assert api_key.scopes == ["*"]
            assert api_key.jti is not None
            assert api_key.token_hash is not None
            assert api_key.expires_at is not None

            # Verify token
            assert isinstance(token, str)
            assert len(token) > 0
            parts = token.split(".")
            assert len(parts) == 3  # JWT format

            # Verify database operations
            db_mock.add.assert_called_once()
            db_mock.commit.assert_called_once()
            db_mock.refresh.assert_called_once()

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_create_api_key_simple_no_expiry(self):
        """Test API key creation without expiration."""
        # Create test user
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Create API key without expiration
            api_key, token = await create_api_key_simple(
                db=db_mock, user=user, label="Permanent Key", expires_in_days=None
            )

            # Verify API key has no expiration
            assert api_key.expires_at is None
            assert isinstance(token, str)

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_create_api_key_simple_invalid_user(self):
        """Test API key creation with invalid user."""
        # Create user without ID
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Should raise ValueError
            with pytest.raises(ValueError, match="User must have a valid ID"):
                await create_api_key_simple(db=db_mock, user=user)

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_create_api_key_simple_invalid_expiry(self):
        """Test API key creation with invalid expiry."""
        # Create test user
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Should raise ValueError for negative expiry
            with pytest.raises(ValueError, match="expires_in_days must be positive"):
                await create_api_key_simple(db=db_mock, user=user, expires_in_days=-1)

    @pytest.mark.asyncio
    async def test_get_api_key_by_id_success(self):
        """Test successful API key retrieval by ID."""
        # Create test API key
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=str(uuid4()),
            token_hash="test_hash",
            label="Test Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Add the API key to the mock database
            db_mock.add(api_key)
            await db_mock.commit()

            result = await get_api_key_by_id(db_mock, 1)

            assert result == api_key
            db_mock.get.assert_called_once_with(ApiKey, 1)

    @pytest.mark.asyncio
    async def test_get_api_key_by_id_not_found(self):
        """Test API key retrieval by ID when not found."""
        # Use new mock database session
        async for db_mock in create_mock_db_session():
            result = await get_api_key_by_id(db_mock, 999)

            assert result is None
            db_mock.get.assert_called_once_with(ApiKey, 999)

    @pytest.mark.asyncio
    async def test_revoke_api_key_simple_success(self):
        """Test successful API key revocation."""
        # Create test API key
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=str(uuid4()),
            token_hash="test_hash",
            label="Test Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
            revoked_at=None,
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Add the API key to the mock database
            db_mock.add(api_key)
            await db_mock.commit()

            result = await revoke_api_key_simple(db_mock, 1)

            assert result is True
            assert api_key.revoked_at is not None
            db_mock.commit.assert_called()

    @pytest.mark.asyncio
    async def test_revoke_api_key_simple_not_found(self):
        """Test API key revocation when key not found."""
        # Use new mock database session
        async for db_mock in create_mock_db_session():
            result = await revoke_api_key_simple(db_mock, 999)

            assert result is False

    @pytest.mark.asyncio
    async def test_revoke_api_key_simple_already_revoked(self):
        """Test API key revocation when already revoked."""
        # Create already revoked API key
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=str(uuid4()),
            token_hash="test_hash",
            label="Test Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
            revoked_at=datetime.now(timezone.utc),
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Add the API key to the mock database
            db_mock.add(api_key)
            await db_mock.commit()

            result = await revoke_api_key_simple(db_mock, 1)

            assert result is False

    @pytest.mark.asyncio
    async def test_get_api_key_by_jti_success(self):
        """Test successful API key retrieval by JTI."""
        jti = str(uuid4())

        # Create test API key
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=jti,
            token_hash="test_hash",
            label="Test Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Add the API key to the mock database
            db_mock.add(api_key)
            await db_mock.commit()

            result = await get_api_key_by_jti(db_mock, jti)

            assert result == api_key

    @pytest.mark.asyncio
    async def test_get_api_key_by_jti_not_found(self):
        """Test API key retrieval by JTI when not found."""
        jti = str(uuid4())

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            result = await get_api_key_by_jti(db_mock, jti)

            assert result is None

    @pytest.mark.asyncio
    async def test_verify_api_key_by_hash_success(self):
        """Test successful API key verification by hash."""
        jti = str(uuid4())
        token_hash = "test_hash"

        # Create active API key
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=jti,
            token_hash=token_hash,
            label="Test Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
            expires_at=None,
            revoked_at=None,
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Mock get_api_key_by_jti
            with patch("app.services.api_key.get_api_key_by_jti") as mock_get_jti:
                mock_get_jti.return_value = api_key

                result = await verify_api_key_by_hash(db_mock, token_hash, jti)

                assert result == api_key

    @pytest.mark.asyncio
    async def test_verify_api_key_by_hash_invalid_hash(self):
        """Test API key verification with invalid hash."""
        jti = str(uuid4())
        token_hash = "test_hash"
        wrong_hash = "wrong_hash"

        # Create active API key
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=jti,
            token_hash=token_hash,
            label="Test Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
            expires_at=None,
            revoked_at=None,
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Mock get_api_key_by_jti
            with patch("app.services.api_key.get_api_key_by_jti") as mock_get_jti:
                mock_get_jti.return_value = api_key

                result = await verify_api_key_by_hash(db_mock, wrong_hash, jti)

                assert result is None

    @pytest.mark.asyncio
    async def test_verify_api_key_by_hash_inactive_key(self):
        """Test API key verification with inactive key."""
        jti = str(uuid4())
        token_hash = "test_hash"

        # Create revoked API key
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=jti,
            token_hash=token_hash,
            label="Test Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
            expires_at=None,
            revoked_at=datetime.now(timezone.utc),  # Revoked
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Mock get_api_key_by_jti
            with patch("app.services.api_key.get_api_key_by_jti") as mock_get_jti:
                mock_get_jti.return_value = api_key

                result = await verify_api_key_by_hash(db_mock, token_hash, jti)

                assert result is None

    @pytest.mark.asyncio
    async def test_update_api_key_last_used_success(self):
        """Test successful API key last used update."""
        # Create API key
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=str(uuid4()),
            token_hash="test_hash",
            label="Test Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
            last_used_at=None,
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            await update_api_key_last_used(db_mock, api_key)

            assert api_key.last_used_at is not None
            db_mock.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_api_key_last_used_throttled(self):
        """Test API key last used update with throttling."""

        # Create API key with recent last used
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=str(uuid4()),
            token_hash="test_hash",
            label="Test Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
            last_used_at=recent_time,
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            await update_api_key_last_used(db_mock, api_key, throttle_minutes=10)

            # Should not update due to throttling
            assert api_key.last_used_at == recent_time
            db_mock.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_api_key_last_used_exception_handling(self):
        """Test API key last used update with exception handling."""
        # Create API key
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=str(uuid4()),
            token_hash="test_hash",
            label="Test Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
            last_used_at=None,
        )

        # Use new mock database session
        async for db_mock in create_mock_db_session():
            # Mock commit error
            db_mock.commit = AsyncMock(side_effect=Exception("Database error"))

            # Should not raise exception
            await update_api_key_last_used(db_mock, api_key)

            db_mock.rollback.assert_called_once()

    @pytest.fixture
    def service(self):
        """Create ApiKeyService instance for testing."""
        from app.services.api_key import ApiKeyService

        return ApiKeyService()

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        from app.tests.mocks import create_mock_current_user

        return create_mock_current_user()

    # NOTE: test_list_user_keys_success and test_list_user_keys_database_error
    # are temporarily commented out due to complex Pydantic validation mocking requirements

    @pytest.mark.asyncio
    async def test_validate_user_key_limit_under_limit(self, service, mock_user):
        """Test key limit validation when under limit."""
        db = AsyncMock()

        # Mock keys - create 5 active keys (under limit of 20)
        mock_keys = []
        for i in range(5):
            key = Mock()
            key.is_active = True
            mock_keys.append(key)

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_keys
        db.execute.return_value = mock_result

        # Should not raise exception
        await service.validate_user_key_limit(db, mock_user.id)

    @pytest.mark.asyncio
    async def test_validate_user_key_limit_at_limit(self, service, mock_user):
        """Test key limit validation when at limit."""
        db = AsyncMock()

        # Mock keys - create 20 active keys (at limit)
        mock_keys = []
        for i in range(20):
            key = Mock()
            key.is_active = True
            mock_keys.append(key)

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_keys
        db.execute.return_value = mock_result

        # Should raise exception
        with pytest.raises(HTTPException) as exc_info:
            await service.validate_user_key_limit(db, mock_user.id)

        assert exc_info.value.status_code == 400
        assert "Maximum number of active API keys (20) reached" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_validate_user_key_limit_mixed_keys(self, service, mock_user):
        """Test key limit validation with mix of active and inactive keys."""
        db = AsyncMock()

        # Mock keys - 15 active, 10 inactive (total 25, but only 15 active)
        mock_keys = []
        for i in range(15):
            key = Mock()
            key.is_active = True
            mock_keys.append(key)
        for i in range(10):
            key = Mock()
            key.is_active = False
            mock_keys.append(key)

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_keys
        db.execute.return_value = mock_result

        # Should not raise exception (only 15 active keys)
        await service.validate_user_key_limit(db, mock_user.id)

    @pytest.mark.asyncio
    async def test_create_api_key_success(self, service, mock_user):
        """Test successful API key creation with limit validation."""
        db = AsyncMock()

        # Mock key limit validation (under limit)
        mock_keys = [Mock(is_active=True) for _ in range(5)]  # 5 active keys
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_keys
        db.execute.return_value = mock_result

        # Mock create_api_key_simple
        with patch("app.services.api_key.create_api_key_simple") as mock_create:
            mock_key = Mock()
            mock_token = "test-token"
            mock_create.return_value = (mock_key, mock_token)

            result = await service.create_api_key(db, mock_user, "Test Key", 30)

            assert result == (mock_key, mock_token)
            mock_create.assert_called_once_with(db, mock_user, "Test Key", 30)

    @pytest.mark.asyncio
    async def test_create_api_key_invalid_user(self, service):
        """Test API key creation with invalid user."""
        db = AsyncMock()
        user = Mock()
        user.id = None

        with pytest.raises(HTTPException) as exc_info:
            await service.create_api_key(db, user, "Test Key", 30)

        assert exc_info.value.status_code == 400
        assert "User must have a valid ID" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_api_key_limit_exceeded(self, service, mock_user):
        """Test API key creation when limit is exceeded."""
        db = AsyncMock()

        # Mock key limit validation (at limit)
        mock_keys = [Mock(is_active=True) for _ in range(20)]  # 20 active keys
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_keys
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await service.create_api_key(db, mock_user, "Test Key", 30)

        assert exc_info.value.status_code == 400
        assert "Maximum number of active API keys (20) reached" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_key_ownership_success(self, service, mock_user):
        """Test successful key ownership verification."""
        db = AsyncMock()

        # Mock API key
        mock_key = Mock()
        mock_key.user_id = mock_user.id
        mock_key.id = 1

        # Mock the repository method
        with patch.object(
            service.api_key_repo, "get_by_user_id_and_key_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_key

            result = await service.verify_key_ownership(db, 1, mock_user.id)

            assert result == mock_key
            mock_get.assert_called_once_with(db, mock_user.id, 1)

    @pytest.mark.asyncio
    async def test_verify_key_ownership_not_found(self, service, mock_user):
        """Test key ownership verification when key not found."""
        db = AsyncMock()

        # Mock the repository method
        with patch.object(
            service.api_key_repo, "get_by_user_id_and_key_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await service.verify_key_ownership(db, 1, mock_user.id)

            assert exc_info.value.status_code == 404
            assert "API key not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_key_ownership_forbidden(self, service, mock_user):
        """Test key ownership verification when user doesn't own key."""
        db = AsyncMock()

        # Mock API key owned by different user
        mock_key = Mock()
        mock_key.user_id = 999  # Different user ID
        mock_key.id = 1

        # Mock the repository method - this should return None for wrong user_id
        with patch.object(
            service.api_key_repo, "get_by_user_id_and_key_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = (
                None  # Repository returns None when user doesn't own the key
            )

            with pytest.raises(HTTPException) as exc_info:
                await service.verify_key_ownership(db, 1, mock_user.id)

            assert exc_info.value.status_code == 404
            assert "API key not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_revoke_user_key_success(self, service, mock_user):
        """Test successful key revocation."""
        db = AsyncMock()

        # Mock API key
        mock_key = Mock()
        mock_key.user_id = mock_user.id
        mock_key.revoked_at = None  # Not revoked yet

        with (
            patch.object(
                service.api_key_repo,
                "get_by_user_id_and_key_id",
                new_callable=AsyncMock,
            ) as mock_get,
            patch("app.services.api_key.revoke_api_key_simple") as mock_revoke,
        ):

            mock_get.return_value = mock_key
            mock_revoke.return_value = True

            result = await service.revoke_user_key(db, 1, mock_user.id)

            assert result is True
            mock_revoke.assert_called_once_with(db, 1)

    @pytest.mark.asyncio
    async def test_revoke_user_key_already_revoked(self, service, mock_user):
        """Test key revocation when key is already revoked."""
        db = AsyncMock()

        # Mock API key that's already revoked
        mock_key = Mock()
        mock_key.user_id = mock_user.id
        mock_key.revoked_at = datetime.now(timezone.utc)  # Already revoked

        with patch.object(
            service.api_key_repo, "get_by_user_id_and_key_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_key

            with pytest.raises(HTTPException) as exc_info:
                await service.revoke_user_key(db, 1, mock_user.id)

            assert exc_info.value.status_code == 400
            assert "API key is already revoked" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_revoke_user_key_revocation_failed(self, service, mock_user):
        """Test key revocation when revocation fails."""
        db = AsyncMock()

        # Mock API key
        mock_key = Mock()
        mock_key.user_id = mock_user.id
        mock_key.revoked_at = None  # Not revoked yet

        with (
            patch.object(
                service.api_key_repo,
                "get_by_user_id_and_key_id",
                new_callable=AsyncMock,
            ) as mock_get,
            patch("app.services.api_key.revoke_api_key_simple") as mock_revoke,
        ):

            mock_get.return_value = mock_key
            mock_revoke.return_value = False  # Revocation failed

            with pytest.raises(HTTPException) as exc_info:
                await service.revoke_user_key(db, 1, mock_user.id)

            assert exc_info.value.status_code == 500
            assert "Failed to revoke API key" in exc_info.value.detail
