"""
Unit tests for the role service.

Tests the role service with various scenarios including
retrieval, existence checks, and error handling.
"""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.exc import SQLAlchemyError

from app.models.role import Role
from app.services.role import RoleService
from app.tests.mocks import create_mock_db_session


class TestRoleService:
    """Test suite for role service."""

    @pytest.fixture
    def role_service(self):
        """Create role service instance for testing."""
        return RoleService()

    @pytest_asyncio.fixture
    async def mock_db_session(self):
        """Create mock database session using new mock utilities."""
        async for db in create_mock_db_session():
            yield db

    @pytest.fixture
    def sample_roles(self):
        """Sample roles for testing."""
        return [
            Role(
                id=1,
                name="admin",
                description="Administrator with full system access",
            ),
            Role(
                id=2,
                name="user",
                description="Standard user with basic access",
            ),
        ]

    @pytest.mark.asyncio
    async def test_get_role_by_name_success(
        self, role_service, mock_db_session, sample_roles
    ):
        """Test successful role retrieval by name."""
        admin_role = sample_roles[0]

        with patch.object(
            role_service.role_repo, "get_by_name", new_callable=AsyncMock
        ) as mock_get_by_name:
            mock_get_by_name.return_value = admin_role

            result = await role_service.get_role_by_name(mock_db_session, "admin")

            assert result == admin_role
            mock_get_by_name.assert_called_once_with(mock_db_session, "admin")

    @pytest.mark.asyncio
    async def test_get_role_by_name_not_found(self, role_service, mock_db_session):
        """Test role retrieval when role doesn't exist."""
        with patch.object(
            role_service.role_repo, "get_by_name", new_callable=AsyncMock
        ) as mock_get_by_name:
            mock_get_by_name.return_value = None

            result = await role_service.get_role_by_name(mock_db_session, "nonexistent")

            assert result is None
            mock_get_by_name.assert_called_once_with(mock_db_session, "nonexistent")

    @pytest.mark.asyncio
    async def test_get_role_by_name_database_error(self, role_service, mock_db_session):
        """Test role retrieval with database error."""
        with patch.object(
            role_service.role_repo, "get_by_name", new_callable=AsyncMock
        ) as mock_get_by_name:
            mock_get_by_name.side_effect = SQLAlchemyError("Database connection failed")

            # The service should raise HTTPException due to error handling decorator
            from fastapi import HTTPException

            with pytest.raises(HTTPException):
                await role_service.get_role_by_name(mock_db_session, "admin")

    @pytest.mark.asyncio
    async def test_get_all_roles_success(
        self, role_service, mock_db_session, sample_roles
    ):
        """Test successful retrieval of all roles."""
        with patch.object(
            role_service.role_repo, "get_all_active", new_callable=AsyncMock
        ) as mock_get_all:
            mock_get_all.return_value = sample_roles

            result = await role_service.get_all_roles(mock_db_session)

            assert result == sample_roles
            assert len(result) == 2
            mock_get_all.assert_called_once_with(mock_db_session)

    @pytest.mark.asyncio
    async def test_get_all_roles_empty(self, role_service, mock_db_session):
        """Test retrieval when no roles exist."""
        with patch.object(
            role_service.role_repo, "get_all_active", new_callable=AsyncMock
        ) as mock_get_all:
            mock_get_all.return_value = []

            result = await role_service.get_all_roles(mock_db_session)

            assert result == []
            mock_get_all.assert_called_once_with(mock_db_session)

    @pytest.mark.asyncio
    async def test_get_all_roles_database_error(self, role_service, mock_db_session):
        """Test get all roles with database error."""
        with patch.object(
            role_service.role_repo, "get_all_active", new_callable=AsyncMock
        ) as mock_get_all:
            mock_get_all.side_effect = SQLAlchemyError("Database connection failed")

            from fastapi import HTTPException

            with pytest.raises(HTTPException):
                await role_service.get_all_roles(mock_db_session)

    @pytest.mark.asyncio
    async def test_role_exists_true(self, role_service, mock_db_session):
        """Test role existence check when role exists."""
        with patch.object(
            role_service.role_repo, "name_exists", new_callable=AsyncMock
        ) as mock_exists:
            mock_exists.return_value = True

            result = await role_service.role_exists(mock_db_session, "admin")

            assert result is True
            mock_exists.assert_called_once_with(mock_db_session, "admin")

    @pytest.mark.asyncio
    async def test_role_exists_false(self, role_service, mock_db_session):
        """Test role existence check when role doesn't exist."""
        with patch.object(
            role_service.role_repo, "name_exists", new_callable=AsyncMock
        ) as mock_exists:
            mock_exists.return_value = False

            result = await role_service.role_exists(mock_db_session, "nonexistent")

            assert result is False
            mock_exists.assert_called_once_with(mock_db_session, "nonexistent")

    @pytest.mark.asyncio
    async def test_role_exists_database_error(self, role_service, mock_db_session):
        """Test role existence check with database error."""
        with patch.object(
            role_service.role_repo, "name_exists", new_callable=AsyncMock
        ) as mock_exists:
            mock_exists.side_effect = SQLAlchemyError("Database connection failed")

            from fastapi import HTTPException

            with pytest.raises(HTTPException):
                await role_service.role_exists(mock_db_session, "admin")

    @pytest.mark.asyncio
    async def test_ensure_default_roles_all_exist(self, role_service, mock_db_session):
        """Test ensure default roles when all roles already exist."""
        with (
            patch.object(
                role_service, "role_exists", new_callable=AsyncMock
            ) as mock_exists,
            patch.object(
                role_service.role_repo, "create", new_callable=AsyncMock
            ) as mock_create,
        ):
            # Mock that both roles exist
            mock_exists.side_effect = [True, True]  # admin, user

            await role_service.ensure_default_roles(mock_db_session)

            # Should check existence of both roles
            assert mock_exists.call_count == 2
            mock_exists.assert_any_call(mock_db_session, "admin")
            mock_exists.assert_any_call(mock_db_session, "user")

            # Should not create any roles
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_default_roles_some_missing(
        self, role_service, mock_db_session
    ):
        """Test ensure default roles when some roles are missing."""
        with (
            patch.object(
                role_service, "role_exists", new_callable=AsyncMock
            ) as mock_exists,
            patch.object(
                role_service.role_repo, "create", new_callable=AsyncMock
            ) as mock_create,
            patch("app.services.role.logger") as mock_logger,
        ):
            # Mock that admin exists but user doesn't
            mock_exists.side_effect = [True, False]  # admin exists, user doesn't

            await role_service.ensure_default_roles(mock_db_session)

            # Should check existence of both roles
            assert mock_exists.call_count == 2

            # Should create only the missing user role
            mock_create.assert_called_once()
            created_role = mock_create.call_args[0][1]  # Second argument is the role
            assert created_role.name == "user"
            assert created_role.description == "Standard user with basic access"

            # Should log the creation
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "Creating default role: user" in log_message

    @pytest.mark.asyncio
    async def test_ensure_default_roles_none_exist(self, role_service, mock_db_session):
        """Test ensure default roles when no roles exist."""
        with (
            patch.object(
                role_service, "role_exists", new_callable=AsyncMock
            ) as mock_exists,
            patch.object(
                role_service.role_repo, "create", new_callable=AsyncMock
            ) as mock_create,
            patch("app.services.role.logger") as mock_logger,
        ):
            # Mock that neither role exists
            mock_exists.side_effect = [False, False]  # Neither admin nor user exists

            await role_service.ensure_default_roles(mock_db_session)

            # Should check existence of both roles
            assert mock_exists.call_count == 2

            # Should create both roles
            assert mock_create.call_count == 2

            # Verify the created roles
            admin_role = mock_create.call_args_list[0][0][1]
            user_role = mock_create.call_args_list[1][0][1]

            assert admin_role.name == "admin"
            assert admin_role.description == "Administrator with full system access"
            assert user_role.name == "user"
            assert user_role.description == "Standard user with basic access"

            # Should log both creations
            assert mock_logger.info.call_count == 2


class TestRoleServiceSingleton:
    """Test role service singleton pattern."""

    def test_role_service_singleton(self):
        """Test that role service uses singleton pattern."""
        from app.services.role import get_role_service, role_service

        # All calls should return the same instance
        service1 = get_role_service()
        service2 = get_role_service()

        assert service1 is service2
        assert service1 is role_service

    def test_role_service_instance_type(self):
        """Test that role service is correct type."""
        from app.services.role import get_role_service

        service = get_role_service()
        assert isinstance(service, RoleService)


class TestRoleServiceErrorHandling:
    """Test role service error handling."""

    @pytest.fixture
    def role_service(self):
        """Create role service instance for testing."""
        return RoleService()

    @pytest_asyncio.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        async for db in create_mock_db_session():
            yield db

    @pytest.mark.asyncio
    async def test_error_handling_decorator_applied(
        self, role_service, mock_db_session
    ):
        """Test that error handling decorators are properly applied."""
        with patch.object(
            role_service.role_repo, "get_by_name", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = SQLAlchemyError("Test database error")

            # Should raise HTTPException due to error handling decorator
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await role_service.get_role_by_name(mock_db_session, "admin")

            # Verify error is properly handled
            assert exc_info.value.status_code == 500  # Internal server error

    @pytest.mark.asyncio
    async def test_repository_error_propagation(self, role_service, mock_db_session):
        """Test that repository errors are properly propagated."""
        with patch.object(
            role_service.role_repo, "get_all_active", new_callable=AsyncMock
        ) as mock_get_all:
            mock_get_all.side_effect = SQLAlchemyError("Connection timeout")

            from fastapi import HTTPException

            with pytest.raises(HTTPException):
                await role_service.get_all_roles(mock_db_session)


class TestRoleServiceLogging:
    """Test role service logging."""

    @pytest.fixture
    def role_service(self):
        """Create role service instance for testing."""
        return RoleService()

    @pytest_asyncio.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        async for db in create_mock_db_session():
            yield db

    @pytest.mark.asyncio
    async def test_ensure_default_roles_logs_creation(
        self, role_service, mock_db_session
    ):
        """Test that role creation is properly logged."""
        with (
            patch.object(
                role_service, "role_exists", new_callable=AsyncMock
            ) as mock_exists,
            patch.object(role_service.role_repo, "create", new_callable=AsyncMock),
            patch("app.services.role.logger") as mock_logger,
        ):
            mock_exists.return_value = False  # Role doesn't exist

            await role_service.ensure_default_roles(mock_db_session)

            # Should log role creation for both default roles
            assert mock_logger.info.call_count == 2

            # Verify log messages
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("Creating default role: admin" in msg for msg in log_calls)
            assert any("Creating default role: user" in msg for msg in log_calls)
