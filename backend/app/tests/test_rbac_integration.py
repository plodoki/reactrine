"""
Integration tests for RBAC system.

Tests the complete RBAC flow from authentication to authorization.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.role import Role
from app.models.user import User
from app.tests.mocks import create_mock_current_admin_user, create_mock_current_user


class TestRBACIntegration:
    """Test RBAC system integration."""

    @pytest.mark.asyncio
    async def test_user_creation_with_default_role(self):
        """Test that new users get default role."""
        from app.schemas.user import UserCreate
        from app.services.user import create_user
        from app.tests.mocks import create_mock_db_session

        user_create = UserCreate(
            email="newuser@example.com",
            password="Test-Password-123!",
            auth_provider="email",
        )

        async for mock_db in create_mock_db_session():
            with (
                patch("app.services.user.UserRepository") as mock_user_repo_class,
                patch("app.services.user.RoleRepository") as mock_role_repo_class,
                patch("app.services.user.get_password_hash") as mock_hash,
            ):
                # Mock repositories
                mock_user_repo = Mock()
                mock_role_repo = Mock()
                mock_user_repo_class.return_value = mock_user_repo
                mock_role_repo_class.return_value = mock_role_repo

                # Mock password hashing
                mock_hash.return_value = "hashed_password"

                # Mock role retrieval
                default_role = Role(id=2, name="user", description="Standard User")
                mock_role_repo.get_by_name = AsyncMock(return_value=default_role)

                # Mock user creation
                created_user = User(
                    id=1,
                    email="newuser@example.com",
                    hashed_password="hashed_password",
                    role_id=2,
                    auth_provider="email",
                )
                mock_user_repo.create = AsyncMock(return_value=created_user)

                # Test user creation
                result = await create_user(mock_db, user_create)

                # Verify user was created with default role
                assert result.email == "newuser@example.com"
                assert result.role_id == 2  # Default user role
                mock_role_repo.get_by_name.assert_called_once_with(mock_db, "user")
                mock_user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_promotion_flow(self):
        """Test promoting user to admin."""
        from app.services.user import assign_user_role
        from app.tests.mocks import create_mock_db_session

        async for mock_db in create_mock_db_session():
            with (
                patch("app.services.user.UserRepository") as mock_user_repo_class,
                patch("app.services.user.RoleRepository") as mock_role_repo_class,
            ):
                # Mock repositories
                mock_user_repo = Mock()
                mock_role_repo = Mock()
                mock_user_repo_class.return_value = mock_user_repo
                mock_role_repo_class.return_value = mock_role_repo

                # Mock role retrieval
                admin_role = Role(id=1, name="admin", description="Administrator")
                mock_role_repo.get_by_name = AsyncMock(return_value=admin_role)

                # Mock user role update
                updated_user = create_mock_current_user()
                updated_user.role_id = 1
                updated_user.role = admin_role
                mock_user_repo.update_user_role = AsyncMock(return_value=updated_user)

                # Test role assignment
                result = await assign_user_role(mock_db, 1, "admin")

                # Verify user was promoted to admin
                assert result.role_id == 1
                assert result.role.name == "admin"
                mock_role_repo.get_by_name.assert_called_once_with(mock_db, "admin")
                mock_user_repo.update_user_role.assert_called_once_with(mock_db, 1, 1)

    def test_endpoint_protection_flow(self, authenticated_client: TestClient):
        """Test that endpoints are properly protected."""
        # Test that regular user cannot access admin endpoints
        response = authenticated_client.get("/api/v1/admin/roles")
        assert response.status_code == 403  # Should get forbidden, not unauthorized
        assert "Access denied" in response.json()["detail"]

        response = authenticated_client.get("/api/v1/admin/users")
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_database_initialization_roles(self):
        """Test that database initialization creates default roles."""
        from app.services.role import RoleService
        from app.tests.mocks import create_mock_db_session

        role_service = RoleService()

        async for mock_db in create_mock_db_session():
            with patch.object(
                role_service.role_repo, "name_exists", new_callable=AsyncMock
            ) as mock_exists:
                with patch.object(
                    role_service.role_repo, "create", new_callable=AsyncMock
                ) as mock_create:
                    # Mock that no roles exist initially
                    mock_exists.return_value = False

                    # Test role initialization
                    await role_service.ensure_default_roles(mock_db)

                    # Verify both default roles were checked and created
                    assert mock_exists.call_count == 2
                    assert mock_create.call_count == 2

                    # Verify the created roles
                    created_roles = [call[0][1] for call in mock_create.call_args_list]
                    role_names = [role.name for role in created_roles]

                    assert "admin" in role_names
                    assert "user" in role_names

    def test_complete_admin_workflow(self, admin_authenticated_client: TestClient):
        """Test complete admin workflow."""
        # Mock the role service and user operations
        mock_roles = [
            Role(id=1, name="admin", description="Administrator"),
            Role(id=2, name="user", description="Standard User"),
        ]

        admin_user = create_mock_current_admin_user()
        regular_user = create_mock_current_user()
        mock_users = [admin_user, regular_user]

        with (
            patch("app.api.v1.endpoints.admin.get_role_service") as mock_get_service,
            patch(
                "app.api.v1.endpoints.admin.get_users_with_roles",
                new_callable=AsyncMock,
            ) as mock_get_users,
            patch(
                "app.api.v1.endpoints.admin.count_total_users",
                new_callable=AsyncMock,
            ) as mock_count_users,
        ):
            mock_service = Mock()
            mock_service.get_all_roles = AsyncMock(return_value=mock_roles)
            mock_get_service.return_value = mock_service
            mock_get_users.return_value = mock_users
            mock_count_users.return_value = len(mock_users)

            # Admin should be able to list roles
            response = admin_authenticated_client.get("/api/v1/admin/roles")
            assert response.status_code == 200

            # Admin should be able to list users
            response = admin_authenticated_client.get("/api/v1/admin/users")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_oauth_user_creation_with_role(self):
        """Test OAuth user creation assigns default role."""
        from app.services.user import create_oauth_user
        from app.tests.mocks import create_mock_db_session

        async for mock_db in create_mock_db_session():
            with (
                patch("app.services.user.UserRepository") as mock_user_repo_class,
                patch("app.services.user.RoleRepository") as mock_role_repo_class,
                patch("app.services.user.get_password_hash") as mock_hash,
            ):
                # Mock repositories
                mock_user_repo = Mock()
                mock_role_repo = Mock()
                mock_user_repo_class.return_value = mock_user_repo
                mock_role_repo_class.return_value = mock_role_repo

                # Mock password hashing
                mock_hash.return_value = "hashed_password"

                # Mock role retrieval
                default_role = Role(id=2, name="user", description="Standard User")
                mock_role_repo.get_by_name = AsyncMock(return_value=default_role)

                # Mock user creation
                created_user = User(
                    id=1,
                    email="oauth@example.com",
                    hashed_password="hashed_password",
                    role_id=2,
                    auth_provider="google",
                )
                mock_user_repo.create = AsyncMock(return_value=created_user)

                # Test OAuth user creation
                result = await create_oauth_user(mock_db, "oauth@example.com", "google")

                # Verify user was created with default role
                assert result.email == "oauth@example.com"
                assert result.role_id == 2  # Default user role
                assert result.auth_provider == "google"
                mock_role_repo.get_by_name.assert_called_once_with(mock_db, "user")

    def test_llm_settings_protection(self, authenticated_client: TestClient):
        """Test that LLM settings endpoints are protected from regular users."""
        # Regular user should not be able to access LLM settings
        response = authenticated_client.get("/api/v1/llm-settings")
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

        response = authenticated_client.post(
            "/api/v1/llm-settings", json={"provider": "openai", "model": "gpt-4"}
        )
        assert response.status_code == 403

    def test_self_protection_prevents_admin_demotion(
        self, admin_authenticated_client: TestClient
    ):
        """Test that admin cannot demote themselves."""
        with patch("app.api.v1.endpoints.admin.get_role_service") as mock_get_service:
            mock_service = Mock()
            mock_role = Role(id=2, name="user", description="Standard User")
            mock_service.get_role_by_name = AsyncMock(return_value=mock_role)
            mock_get_service.return_value = mock_service

            # Admin (ID 2) trying to change their own role should fail
            response = admin_authenticated_client.put(
                "/api/v1/admin/users/2/role",
                json={"role_name": "user"},
            )
            assert response.status_code == 400
            assert "Cannot modify your own role" in response.json()["detail"]

    def test_role_based_navigation_data(self, admin_authenticated_client: TestClient):
        """Test that user data includes role information for navigation."""
        # Mock get_user_by_email_with_role for the auth endpoint
        admin_user = create_mock_current_admin_user()

        with patch(
            "app.services.user.get_user_by_email_with_role", new_callable=AsyncMock
        ) as mock_get_user:
            mock_get_user.return_value = admin_user

            response = admin_authenticated_client.get("/api/v1/auth/me")
            assert response.status_code == 200

            data = response.json()
            assert "role" in data
            assert data["role"]["name"] == "admin"


class TestRBACErrorScenarios:
    """Test RBAC error conditions and edge cases."""

    def test_missing_role_in_database(self, authenticated_client: TestClient):
        """Test behavior when user has no role assigned."""
        # Mock a user without a role
        with patch(
            "app.api.rbac.get_user_by_email_with_role", new_callable=AsyncMock
        ) as mock_get_user:
            mock_user = create_mock_current_user()
            mock_user.role = None  # User has no role
            mock_get_user.return_value = mock_user

            response = authenticated_client.get("/api/v1/admin/roles")
            assert response.status_code == 403
            assert "Access denied: No role assigned" in response.json()["detail"]

    def test_user_not_found_in_role_check(self, authenticated_client: TestClient):
        """Test behavior when user is not found during role check."""
        with patch(
            "app.api.rbac.get_user_by_email_with_role", new_callable=AsyncMock
        ) as mock_get_user:
            mock_get_user.return_value = None  # User not found

            response = authenticated_client.get("/api/v1/admin/roles")
            assert response.status_code == 403
            assert "Access denied: No role assigned" in response.json()["detail"]

    def test_invalid_role_assignment(self, admin_authenticated_client: TestClient):
        """Test assignment of non-existent role."""
        with patch(
            "app.api.v1.endpoints.admin.assign_user_role", new_callable=AsyncMock
        ) as mock_assign:
            # Mock assign_user_role to raise ValueError for invalid role
            mock_assign.side_effect = ValueError("Role 'nonexistent' not found")

            response = admin_authenticated_client.put(
                "/api/v1/admin/users/1/role", json={"role_name": "nonexistent"}
            )

            assert response.status_code == 400
            assert "Role 'nonexistent' not found" in response.json()["detail"]


class TestRBACPerformance:
    """Test RBAC performance characteristics."""

    def test_role_loading_efficiency(self, admin_authenticated_client: TestClient):
        """Test that roles are efficiently loaded with users."""
        with patch("app.repositories.user.UserRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_admin = create_mock_current_admin_user()
            mock_repo.get_by_id_with_role = AsyncMock(return_value=mock_admin)
            mock_repo_class.return_value = mock_repo

            response = admin_authenticated_client.get("/api/v1/admin/users/1")
            assert response.status_code == 200

            # Verify that get_by_id_with_role was called (efficient role loading)
            mock_repo.get_by_id_with_role.assert_called_once()

    def test_bulk_user_operations(self, admin_authenticated_client: TestClient):
        """Test bulk user operations maintain efficiency."""
        mock_users = [create_mock_current_user() for _ in range(10)]

        with (
            patch(
                "app.api.v1.endpoints.admin.get_users_with_roles",
                new_callable=AsyncMock,
            ) as mock_get_users,
            patch(
                "app.api.v1.endpoints.admin.count_total_users",
                new_callable=AsyncMock,
            ) as mock_count_users,
        ):
            mock_get_users.return_value = mock_users
            mock_count_users.return_value = 10

            response = admin_authenticated_client.get("/api/v1/admin/users?limit=10")
            assert response.status_code == 200

            data = response.json()
            assert len(data["users"]) == 10

            # Verify single database query for bulk operation
            mock_get_users.assert_called_once()
