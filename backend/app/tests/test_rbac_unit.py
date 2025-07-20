"""
Unit tests for RBAC (Role-Based Access Control) system.

Tests the RBAC utilities, RoleRequired factory, and helper functions.
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException, status

from app.api.rbac import AdminOnly, RoleRequired, get_user_role, has_role, is_admin
from app.tests.mocks import create_mock_current_admin_user, create_mock_current_user


class TestRoleRequired:
    """Test RoleRequired factory function."""

    @pytest.mark.asyncio
    async def test_role_required_single_role_success(self):
        """Test successful authorization with single required role."""
        # Create mock user with admin role
        mock_user = create_mock_current_admin_user()

        # Create mock dependency
        async def mock_get_current_active_user():
            return mock_user

        async def mock_get_user_by_email_with_role(db, email):
            return mock_user

        # Create role requirement for admin
        admin_required = RoleRequired("admin")

        with (
            patch("app.api.rbac.get_current_active_user", mock_get_current_active_user),
            patch(
                "app.api.rbac.get_user_by_email_with_role",
                mock_get_user_by_email_with_role,
            ),
        ):
            # Should succeed for admin user
            result = await admin_required(mock_user, None)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_role_required_multiple_roles_success(self):
        """Test successful authorization with multiple allowed roles."""
        # Create mock user with user role
        mock_user = create_mock_current_user()

        async def mock_get_current_active_user():
            return mock_user

        async def mock_get_user_by_email_with_role(db, email):
            return mock_user

        # Create role requirement for user or admin
        user_or_admin = RoleRequired("user", "admin")

        with (
            patch("app.api.rbac.get_current_active_user", mock_get_current_active_user),
            patch(
                "app.api.rbac.get_user_by_email_with_role",
                mock_get_user_by_email_with_role,
            ),
        ):
            # Should succeed for user role
            result = await user_or_admin(mock_user, None)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_role_required_unauthorized_role(self):
        """Test authorization failure with unauthorized role."""
        # Create mock user with user role
        mock_user = create_mock_current_user()

        async def mock_get_current_active_user():
            return mock_user

        async def mock_get_user_by_email_with_role(db, email):
            return mock_user

        # Create role requirement for admin only
        admin_only = RoleRequired("admin")

        with (
            patch("app.api.rbac.get_current_active_user", mock_get_current_active_user),
            patch(
                "app.api.rbac.get_user_by_email_with_role",
                mock_get_user_by_email_with_role,
            ),
        ):
            # Should fail for user role trying to access admin endpoint
            with pytest.raises(HTTPException) as exc_info:
                await admin_only(mock_user, None)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Access denied: Insufficient permissions" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_role_required_no_role_assigned(self):
        """Test authorization failure when user has no role."""
        # Create mock user without role
        mock_user = create_mock_current_user()
        mock_user.role = None

        async def mock_get_current_active_user():
            return mock_user

        async def mock_get_user_by_email_with_role(db, email):
            return mock_user

        admin_only = RoleRequired("admin")

        with (
            patch("app.api.rbac.get_current_active_user", mock_get_current_active_user),
            patch(
                "app.api.rbac.get_user_by_email_with_role",
                mock_get_user_by_email_with_role,
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await admin_only(mock_user, None)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Access denied: No role assigned" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_role_required_user_not_found(self):
        """Test authorization failure when user is not found in database."""
        mock_user = create_mock_current_user()

        async def mock_get_current_active_user():
            return mock_user

        async def mock_get_user_by_email_with_role(db, email):
            return None  # User not found

        admin_only = RoleRequired("admin")

        with (
            patch("app.api.rbac.get_current_active_user", mock_get_current_active_user),
            patch(
                "app.api.rbac.get_user_by_email_with_role",
                mock_get_user_by_email_with_role,
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await admin_only(mock_user, None)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Access denied: No role assigned" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_role_required_case_insensitive_success(self):
        """Test successful authorization with mixed-case roles."""
        # Create mock user with admin role (lowercase)
        mock_user = create_mock_current_admin_user()

        async def mock_get_current_active_user():
            return mock_user

        async def mock_get_user_by_email_with_role(db, email):
            return mock_user

        # Test with uppercase required role
        admin_required = RoleRequired("ADMIN")

        with (
            patch("app.api.rbac.get_current_active_user", mock_get_current_active_user),
            patch(
                "app.api.rbac.get_user_by_email_with_role",
                mock_get_user_by_email_with_role,
            ),
        ):
            # Should succeed for admin user with uppercase required role
            result = await admin_required(mock_user, None)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_role_required_mixed_case_success(self):
        """Test successful authorization with mixed-case user and required roles."""
        # Create mock user with mixed-case role
        mock_user = create_mock_current_user()
        mock_user.role.name = "User"  # Mixed case

        async def mock_get_current_active_user():
            return mock_user

        async def mock_get_user_by_email_with_role(db, email):
            return mock_user

        # Test with different case required role
        user_required = RoleRequired("USER")

        with (
            patch("app.api.rbac.get_current_active_user", mock_get_current_active_user),
            patch(
                "app.api.rbac.get_user_by_email_with_role",
                mock_get_user_by_email_with_role,
            ),
        ):
            # Should succeed despite case differences
            result = await user_required(mock_user, None)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_role_required_multiple_mixed_case_success(self):
        """Test successful authorization with multiple mixed-case roles."""
        # Create mock user with admin role
        mock_user = create_mock_current_admin_user()
        mock_user.role.name = "Admin"  # Mixed case

        async def mock_get_current_active_user():
            return mock_user

        async def mock_get_user_by_email_with_role(db, email):
            return mock_user

        # Test with multiple mixed-case required roles
        multi_role_required = RoleRequired("user", "ADMIN", "Moderator")

        with (
            patch("app.api.rbac.get_current_active_user", mock_get_current_active_user),
            patch(
                "app.api.rbac.get_user_by_email_with_role",
                mock_get_user_by_email_with_role,
            ),
        ):
            # Should succeed with admin role matching one of the required roles
            result = await multi_role_required(mock_user, None)
            assert result == mock_user


class TestRoleAliases:
    """Test role requirement aliases."""

    @pytest.mark.asyncio
    async def test_admin_only_alias(self):
        """Test AdminOnly alias works correctly."""
        mock_admin = create_mock_current_admin_user()

        async def mock_get_current_active_user():
            return mock_admin

        async def mock_get_user_by_email_with_role(db, email):
            return mock_admin

        with (
            patch("app.api.rbac.get_current_active_user", mock_get_current_active_user),
            patch(
                "app.api.rbac.get_user_by_email_with_role",
                mock_get_user_by_email_with_role,
            ),
        ):
            result = await AdminOnly(mock_admin, None)
            assert result == mock_admin


class TestRoleHelpers:
    """Test role helper functions."""

    def test_get_user_role_success(self):
        """Test successful role retrieval."""
        user = create_mock_current_user()
        role_name = get_user_role(user)
        assert role_name == "user"

    def test_get_user_role_no_role(self):
        """Test role retrieval when user has no role."""
        user = create_mock_current_user()
        user.role = None

        with pytest.raises(ValueError, match="User has no role assigned"):
            get_user_role(user)

    def test_is_admin_true(self):
        """Test is_admin returns True for admin user."""
        admin_user = create_mock_current_admin_user()
        assert is_admin(admin_user) is True

    def test_is_admin_false(self):
        """Test is_admin returns False for non-admin user."""
        regular_user = create_mock_current_user()
        assert is_admin(regular_user) is False

    def test_is_admin_no_role(self):
        """Test is_admin returns False when user has no role."""
        user = create_mock_current_user()
        user.role = None
        assert is_admin(user) is False

    def test_has_role_true(self):
        """Test has_role returns True when user has specified role."""
        user = create_mock_current_user()
        assert has_role(user, "user") is True

    def test_has_role_false(self):
        """Test has_role returns False when user doesn't have specified role."""
        user = create_mock_current_user()
        assert has_role(user, "admin") is False

    def test_has_role_no_role(self):
        """Test has_role returns False when user has no role."""
        user = create_mock_current_user()
        user.role = None
        assert has_role(user, "user") is False


class TestRBACLogging:
    """Test RBAC logging functionality."""

    @pytest.mark.asyncio
    async def test_rbac_logs_successful_authorization(self):
        """Test that successful authorization is logged."""
        mock_user = create_mock_current_admin_user()

        async def mock_get_current_active_user():
            return mock_user

        async def mock_get_user_by_email_with_role(db, email):
            return mock_user

        admin_only = RoleRequired("admin")

        with (
            patch("app.api.rbac.get_current_active_user", mock_get_current_active_user),
            patch(
                "app.api.rbac.get_user_by_email_with_role",
                mock_get_user_by_email_with_role,
            ),
            patch("app.api.rbac.logger") as mock_logger,
        ):
            await admin_only(mock_user, None)

            # Verify debug log was called for successful authorization
            mock_logger.debug.assert_called_once()
            debug_call = mock_logger.debug.call_args[0][0]
            assert "granted access" in debug_call
            assert mock_user.email in debug_call

    @pytest.mark.asyncio
    async def test_rbac_logs_failed_authorization(self):
        """Test that failed authorization is logged."""
        mock_user = create_mock_current_user()  # user role

        async def mock_get_current_active_user():
            return mock_user

        async def mock_get_user_by_email_with_role(db, email):
            return mock_user

        admin_only = RoleRequired("admin")

        with (
            patch("app.api.rbac.get_current_active_user", mock_get_current_active_user),
            patch(
                "app.api.rbac.get_user_by_email_with_role",
                mock_get_user_by_email_with_role,
            ),
            patch("app.api.rbac.logger") as mock_logger,
        ):
            with pytest.raises(HTTPException):
                await admin_only(mock_user, None)

            # Verify warning log was called for failed authorization
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "attempted to access endpoint" in warning_call
            assert mock_user.email in warning_call
