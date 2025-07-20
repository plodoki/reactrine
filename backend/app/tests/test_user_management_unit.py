"""Tests for user management functionality including status updates and deletion."""

from unittest.mock import AsyncMock

import pytest

from app.repositories.user import UserRepository
from app.services.user import delete_user, disable_user, enable_user
from app.tests.mocks.database import create_mock_db_session
from app.tests.mocks.users import MockUserData, create_mock_user


class TestUserRepositoryManagement:
    """Test class for user repository management operations."""

    @pytest.fixture
    def user_repo(self):
        """Create a UserRepository instance."""
        return UserRepository()

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        return create_mock_user()

    @pytest.fixture
    def mock_admin_user(self):
        """Create a mock admin user."""
        admin_data = MockUserData.get_admin_user()
        return create_mock_user(admin_data)

    @pytest.mark.asyncio
    async def test_soft_delete_user_success(self, user_repo, mock_user):
        """Test successful user soft deletion (disable)."""
        # Use new mock database session pattern
        async for mock_db in create_mock_db_session():
            # Mock repository methods
            user_repo.get_by_id = AsyncMock(return_value=mock_user)
            user_repo.update = AsyncMock(return_value=mock_user)

            # Call the method
            result = await user_repo.soft_delete_user(mock_db, 1)

            # Assertions
            assert result == mock_user
            assert result.is_active is False
            user_repo.get_by_id.assert_called_once_with(mock_db, 1)
            user_repo.update.assert_called_once_with(mock_db, mock_user)

    @pytest.mark.asyncio
    async def test_soft_delete_user_not_found(self, user_repo):
        """Test soft deletion when user not found."""
        # Use new mock database session pattern
        async for mock_db in create_mock_db_session():
            # Mock repository methods
            user_repo.get_by_id = AsyncMock(return_value=None)
            user_repo.update = AsyncMock()

            # Call the method
            result = await user_repo.soft_delete_user(mock_db, 999)

            # Assertions
            assert result is None
            user_repo.get_by_id.assert_called_once_with(mock_db, 999)
            user_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_activate_user_success(self, user_repo, mock_user):
        """Test successful user activation."""
        # Set user as inactive initially
        mock_user.is_active = False

        # Use new mock database session pattern
        async for mock_db in create_mock_db_session():
            # Mock repository methods
            user_repo.get_by_id = AsyncMock(return_value=mock_user)
            user_repo.update = AsyncMock(return_value=mock_user)

            # Call the method
            result = await user_repo.activate_user(mock_db, 1)

            # Assertions
            assert result == mock_user
            assert result.is_active is True
            user_repo.get_by_id.assert_called_once_with(mock_db, 1)
            user_repo.update.assert_called_once_with(mock_db, mock_user)

    @pytest.mark.asyncio
    async def test_activate_user_not_found(self, user_repo):
        """Test activation when user not found."""
        # Use new mock database session pattern
        async for mock_db in create_mock_db_session():
            # Mock repository methods
            user_repo.get_by_id = AsyncMock(return_value=None)
            user_repo.update = AsyncMock()

            # Call the method
            result = await user_repo.activate_user(mock_db, 999)

            # Assertions
            assert result is None
            user_repo.get_by_id.assert_called_once_with(mock_db, 999)
            user_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_hard_delete_user_success(self, user_repo, mock_user):
        """Test successful user hard deletion."""
        # Use new mock database session pattern
        async for mock_db in create_mock_db_session():
            # Mock repository method
            user_repo.get_by_id = AsyncMock(return_value=mock_user)

            # Call the method
            result = await user_repo.hard_delete_user(mock_db, 1)

            # Assertions
            assert result is True
            user_repo.get_by_id.assert_called_once_with(mock_db, 1)
            mock_db.delete.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_hard_delete_user_not_found(self, user_repo):
        """Test hard deletion when user not found."""
        # Use new mock database session pattern
        async for mock_db in create_mock_db_session():
            # Mock repository methods
            user_repo.get_by_id = AsyncMock(return_value=None)

            # Call the method
            result = await user_repo.hard_delete_user(mock_db, 999)

            # Assertions
            assert result is False
            user_repo.get_by_id.assert_called_once_with(mock_db, 999)
            mock_db.delete.assert_not_called()
            mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_hard_delete_user_database_error(self, user_repo, mock_user):
        """Test hard deletion with database error and rollback."""
        from sqlalchemy.exc import SQLAlchemyError

        # Use new mock database session pattern
        async for mock_db in create_mock_db_session():
            # Mock repository and database methods
            user_repo.get_by_id = AsyncMock(return_value=mock_user)
            mock_db.delete = AsyncMock(side_effect=SQLAlchemyError("Database error"))

            # Call the method and expect exception
            with pytest.raises(SQLAlchemyError):
                await user_repo.hard_delete_user(mock_db, 1)

            # Assertions
            user_repo.get_by_id.assert_called_once_with(mock_db, 1)
            mock_db.delete.assert_called_once_with(mock_user)


class TestUserServiceManagement:
    """Test class for user service management operations."""

    @pytest.fixture
    async def mock_db(self):
        """Create a mock database session."""
        async for session in create_mock_db_session():
            yield session

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        return create_mock_user()

    @pytest.mark.asyncio
    async def test_disable_user_success(self, mock_db, mock_user, monkeypatch):
        """Test successful user disabling through service."""
        # Mock UserRepository
        mock_repo = AsyncMock()
        mock_repo.soft_delete_user = AsyncMock(return_value=mock_user)

        # Patch the UserRepository class
        monkeypatch.setattr("app.services.user.UserRepository", lambda: mock_repo)

        # Call the service method
        result = await disable_user(mock_db, 1)

        # Assertions
        assert result == mock_user
        mock_repo.soft_delete_user.assert_called_once_with(mock_db, 1)

    @pytest.mark.asyncio
    async def test_enable_user_success(self, mock_db, mock_user, monkeypatch):
        """Test successful user enabling through service."""
        # Mock UserRepository
        mock_repo = AsyncMock()
        mock_repo.activate_user = AsyncMock(return_value=mock_user)

        # Patch the UserRepository class
        monkeypatch.setattr("app.services.user.UserRepository", lambda: mock_repo)

        # Call the service method
        result = await enable_user(mock_db, 1)

        # Assertions
        assert result == mock_user
        mock_repo.activate_user.assert_called_once_with(mock_db, 1)

    @pytest.mark.asyncio
    async def test_delete_user_success(self, mock_db, mock_user, monkeypatch):
        """Test successful user deletion through service."""
        # Mock UserRepository
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_user)
        mock_repo.hard_delete_user = AsyncMock(return_value=True)

        # Patch the UserRepository class
        monkeypatch.setattr("app.services.user.UserRepository", lambda: mock_repo)

        # Call the service method
        result = await delete_user(mock_db, 1)

        # Assertions
        assert result is True
        mock_repo.get_by_id.assert_called_once_with(mock_db, 1)
        mock_repo.hard_delete_user.assert_called_once_with(mock_db, 1)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, mock_db, monkeypatch):
        """Test user deletion when user not found."""
        # Mock UserRepository
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=None)
        mock_repo.hard_delete_user = AsyncMock()

        # Patch the UserRepository class
        monkeypatch.setattr("app.services.user.UserRepository", lambda: mock_repo)

        # Call the service method
        result = await delete_user(mock_db, 999)

        # Assertions
        assert result is False
        mock_repo.get_by_id.assert_called_once_with(mock_db, 999)
        mock_repo.hard_delete_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_disable_user_not_found(self, mock_db, monkeypatch):
        """Test disabling user when user not found."""
        # Mock UserRepository
        mock_repo = AsyncMock()
        mock_repo.soft_delete_user = AsyncMock(return_value=None)

        # Patch the UserRepository class
        monkeypatch.setattr("app.services.user.UserRepository", lambda: mock_repo)

        # Call the service method
        result = await disable_user(mock_db, 999)

        # Assertions
        assert result is None
        mock_repo.soft_delete_user.assert_called_once_with(mock_db, 999)

    @pytest.mark.asyncio
    async def test_enable_user_not_found(self, mock_db, monkeypatch):
        """Test enabling user when user not found."""
        # Mock UserRepository
        mock_repo = AsyncMock()
        mock_repo.activate_user = AsyncMock(return_value=None)

        # Patch the UserRepository class
        monkeypatch.setattr("app.services.user.UserRepository", lambda: mock_repo)

        # Call the service method
        result = await enable_user(mock_db, 999)

        # Assertions
        assert result is None
        mock_repo.activate_user.assert_called_once_with(mock_db, 999)
