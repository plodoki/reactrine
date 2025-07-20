"""
Unit tests for the role repository.

Tests the role repository with various scenarios including
CRUD operations, search functionality, and error handling.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from sqlalchemy.exc import SQLAlchemyError

from app.models.role import Role
from app.repositories.role import RoleRepository
from app.tests.mocks import create_mock_db_session


class TestRoleRepository:
    """Test suite for role repository."""

    @pytest.fixture
    def role_repo(self):
        """Create role repository instance for testing."""
        return RoleRepository()

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
    async def test_get_by_name_success(self, role_repo, mock_db_session, sample_roles):
        """Test successful role retrieval by name."""
        admin_role = sample_roles[0]

        # Mock database execute to return the role
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = admin_role
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await role_repo.get_by_name(mock_db_session, "admin")

        assert result == admin_role
        mock_db_session.execute.assert_called_once()

        # Verify the SQL query was properly constructed
        query_arg = mock_db_session.execute.call_args[0][0]
        assert (
            str(query_arg).lower().find("role.name") != -1
        )  # Contains role.name filter

    @pytest.mark.asyncio
    async def test_get_by_name_case_insensitive(
        self, role_repo, mock_db_session, sample_roles
    ):
        """Test case-insensitive role retrieval by name."""
        admin_role = sample_roles[0]

        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = admin_role
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Test with different case variations
        result = await role_repo.get_by_name(mock_db_session, "ADMIN")
        assert result == admin_role

        result = await role_repo.get_by_name(mock_db_session, "Admin")
        assert result == admin_role

        result = await role_repo.get_by_name(mock_db_session, "aDmIn")
        assert result == admin_role

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, role_repo, mock_db_session):
        """Test role retrieval when role doesn't exist."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await role_repo.get_by_name(mock_db_session, "nonexistent")

        assert result is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_name_database_error(self, role_repo, mock_db_session):
        """Test role retrieval with database error."""
        mock_db_session.execute = AsyncMock(
            side_effect=SQLAlchemyError("Database connection failed")
        )

        with pytest.raises(SQLAlchemyError):
            await role_repo.get_by_name(mock_db_session, "admin")

    @pytest.mark.asyncio
    async def test_get_all_active_success(
        self, role_repo, mock_db_session, sample_roles
    ):
        """Test successful retrieval of all active roles."""
        # Mock the parent get_all method
        with patch.object(role_repo, "get_all", new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = sample_roles

            result = await role_repo.get_all_active(mock_db_session)

            assert result == sample_roles
            assert len(result) == 2
            mock_get_all.assert_called_once_with(mock_db_session)

    @pytest.mark.asyncio
    async def test_get_all_active_empty(self, role_repo, mock_db_session):
        """Test retrieval when no roles exist."""
        with patch.object(role_repo, "get_all", new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = []

            result = await role_repo.get_all_active(mock_db_session)

            assert result == []
            mock_get_all.assert_called_once_with(mock_db_session)

    @pytest.mark.asyncio
    async def test_get_all_active_database_error(self, role_repo, mock_db_session):
        """Test get all active roles with database error."""
        with patch.object(role_repo, "get_all", new_callable=AsyncMock) as mock_get_all:
            mock_get_all.side_effect = SQLAlchemyError("Database connection failed")

            with pytest.raises(SQLAlchemyError):
                await role_repo.get_all_active(mock_db_session)

    @pytest.mark.asyncio
    async def test_name_exists_true(self, role_repo, mock_db_session, sample_roles):
        """Test name existence check when role exists."""
        admin_role = sample_roles[0]

        with patch.object(
            role_repo, "get_by_name", new_callable=AsyncMock
        ) as mock_get_by_name:
            mock_get_by_name.return_value = admin_role

            result = await role_repo.name_exists(mock_db_session, "admin")

            assert result is True
            mock_get_by_name.assert_called_once_with(mock_db_session, "admin")

    @pytest.mark.asyncio
    async def test_name_exists_false(self, role_repo, mock_db_session):
        """Test name existence check when role doesn't exist."""
        with patch.object(
            role_repo, "get_by_name", new_callable=AsyncMock
        ) as mock_get_by_name:
            mock_get_by_name.return_value = None

            result = await role_repo.name_exists(mock_db_session, "nonexistent")

            assert result is False
            mock_get_by_name.assert_called_once_with(mock_db_session, "nonexistent")

    @pytest.mark.asyncio
    async def test_name_exists_database_error(self, role_repo, mock_db_session):
        """Test name existence check with database error."""
        with patch.object(
            role_repo, "get_by_name", new_callable=AsyncMock
        ) as mock_get_by_name:
            mock_get_by_name.side_effect = SQLAlchemyError("Database connection failed")

            with pytest.raises(SQLAlchemyError):
                await role_repo.name_exists(mock_db_session, "admin")

    @pytest.mark.asyncio
    async def test_create_role_success(self, role_repo, mock_db_session):
        """Test successful role creation."""
        new_role = Role(name="moderator", description="Moderator role")

        with patch.object(role_repo, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = new_role

            result = await role_repo.create(mock_db_session, new_role)

            assert result == new_role
            mock_create.assert_called_once_with(mock_db_session, new_role)

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, role_repo, mock_db_session, sample_roles):
        """Test successful role retrieval by ID."""
        admin_role = sample_roles[0]

        with patch.object(
            role_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get_by_id:
            mock_get_by_id.return_value = admin_role

            result = await role_repo.get_by_id(mock_db_session, 1)

            assert result == admin_role
            mock_get_by_id.assert_called_once_with(mock_db_session, 1)

    @pytest.mark.asyncio
    async def test_update_role_success(self, role_repo, mock_db_session, sample_roles):
        """Test successful role update."""
        admin_role = sample_roles[0]
        admin_role.description = "Updated description"

        with patch.object(role_repo, "update", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = admin_role

            result = await role_repo.update(mock_db_session, admin_role)

            assert result == admin_role
            assert result.description == "Updated description"
            mock_update.assert_called_once_with(mock_db_session, admin_role)

    @pytest.mark.asyncio
    async def test_delete_role_success(self, role_repo, mock_db_session, sample_roles):
        """Test successful role deletion."""
        admin_role = sample_roles[0]

        with patch.object(role_repo, "delete", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            result = await role_repo.delete(mock_db_session, admin_role)

            assert result is True
            mock_delete.assert_called_once_with(mock_db_session, admin_role)


class TestRoleRepositoryInheritance:
    """Test that RoleRepository properly inherits from BaseRepository."""

    def test_inheritance(self):
        """Test that RoleRepository inherits from BaseRepository."""
        from app.repositories.base import BaseRepository

        role_repo = RoleRepository()
        assert isinstance(role_repo, BaseRepository)

    def test_model_type(self):
        """Test that RoleRepository is properly typed for Role model."""
        role_repo = RoleRepository()
        # The repository should be initialized with Role as the model type
        assert role_repo.model == Role

    def test_available_methods(self):
        """Test that all required methods are available."""
        role_repo = RoleRepository()

        # Methods from BaseRepository
        assert hasattr(role_repo, "create")
        assert hasattr(role_repo, "get_by_id")
        assert hasattr(role_repo, "get_all")
        assert hasattr(role_repo, "update")
        assert hasattr(role_repo, "delete")

        # Custom methods from RoleRepository
        assert hasattr(role_repo, "get_by_name")
        assert hasattr(role_repo, "get_all_active")
        assert hasattr(role_repo, "name_exists")


class TestRoleRepositoryLogging:
    """Test role repository logging functionality."""

    @pytest.fixture
    def role_repo(self):
        """Create role repository instance for testing."""
        return RoleRepository()

    @pytest_asyncio.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        async for db in create_mock_db_session():
            yield db

    @pytest.mark.asyncio
    async def test_error_logging(self, role_repo, mock_db_session):
        """Test that database errors are properly logged."""
        mock_db_session.execute = AsyncMock(side_effect=SQLAlchemyError("Test error"))

        with patch("app.repositories.role.logger") as mock_logger:
            with pytest.raises(SQLAlchemyError):
                await role_repo.get_by_name(mock_db_session, "admin")

            # Verify error was logged
            mock_logger.error.assert_called_once()
            log_message = mock_logger.error.call_args[0][0]
            assert "Database error getting role by name admin" in log_message

    @pytest.mark.asyncio
    async def test_get_all_active_error_logging(self, role_repo, mock_db_session):
        """Test error logging for get_all_active method."""
        with (
            patch.object(role_repo, "get_all", new_callable=AsyncMock) as mock_get_all,
            patch("app.repositories.role.logger") as mock_logger,
        ):
            mock_get_all.side_effect = SQLAlchemyError("Test error")

            with pytest.raises(SQLAlchemyError):
                await role_repo.get_all_active(mock_db_session)

            mock_logger.error.assert_called_once()
            log_message = mock_logger.error.call_args[0][0]
            assert "Database error getting all active roles" in log_message

    @pytest.mark.asyncio
    async def test_name_exists_error_logging(self, role_repo, mock_db_session):
        """Test error logging for name_exists method."""
        with (
            patch.object(
                role_repo, "get_by_name", new_callable=AsyncMock
            ) as mock_get_by_name,
            patch("app.repositories.role.logger") as mock_logger,
        ):
            mock_get_by_name.side_effect = SQLAlchemyError("Test error")

            with pytest.raises(SQLAlchemyError):
                await role_repo.name_exists(mock_db_session, "admin")

            mock_logger.error.assert_called_once()
            log_message = mock_logger.error.call_args[0][0]
            assert "Database error checking if role name exists admin" in log_message


class TestRoleRepositoryEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def role_repo(self):
        """Create role repository instance for testing."""
        return RoleRepository()

    @pytest_asyncio.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        async for db in create_mock_db_session():
            yield db

    @pytest.mark.asyncio
    async def test_get_by_name_empty_string(self, role_repo, mock_db_session):
        """Test role retrieval with empty string."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await role_repo.get_by_name(mock_db_session, "")

        assert result is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_name_whitespace_only(self, role_repo, mock_db_session):
        """Test role retrieval with whitespace-only string."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await role_repo.get_by_name(mock_db_session, "   ")

        assert result is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_name_very_long_string(self, role_repo, mock_db_session):
        """Test role retrieval with very long string."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        long_name = "a" * 1000  # Very long role name
        result = await role_repo.get_by_name(mock_db_session, long_name)

        assert result is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_name_special_characters(self, role_repo, mock_db_session):
        """Test role retrieval with special characters."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        special_name = "role-with_special.chars@123"
        result = await role_repo.get_by_name(mock_db_session, special_name)

        assert result is None
        mock_db_session.execute.assert_called_once()
