"""
Tests for admin API endpoints.

These tests verify the admin endpoints work correctly with RBAC.
"""

from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

from app.models.role import Role
from app.tests.mocks import MockUserData, create_mock_user


class TestAdminEndpoints:
    """Test admin REST endpoints."""

    def test_list_roles_requires_admin(self, client: TestClient):
        """Test that GET /admin/roles requires admin role."""
        # Test without authentication - should get 401
        response = client.get("/api/v1/admin/roles")
        assert response.status_code == 401

    def test_list_roles_success(self, admin_authenticated_client: TestClient):
        """Test successful role listing."""
        # Mock role service
        mock_roles = [
            Role(id=1, name="admin", description="Administrator"),
            Role(id=2, name="user", description="Standard User"),
        ]

        with patch("app.api.v1.endpoints.admin.get_role_service") as mock_get_service:
            mock_service = Mock()
            mock_service.get_all_roles = AsyncMock(return_value=mock_roles)
            mock_get_service.return_value = mock_service

            response = admin_authenticated_client.get("/api/v1/admin/roles")
            assert response.status_code == 200

            data = response.json()
            assert "roles" in data
            assert "total" in data
            assert data["total"] == 2
            assert len(data["roles"]) == 2
            assert data["roles"][0]["name"] == "admin"
            assert data["roles"][1]["name"] == "user"

    def test_list_users_requires_admin(self, client: TestClient):
        """Test that GET /admin/users requires admin role."""
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401

    def test_list_users_success(self, admin_authenticated_client: TestClient):
        """Test successful user listing."""
        # Create proper User model instances
        admin_user = create_mock_user(MockUserData.get_admin_user())
        regular_user = create_mock_user(MockUserData.get_default_user())
        mock_users = [admin_user, regular_user]

        with (
            patch(
                "app.api.v1.endpoints.admin.get_users_with_roles",
                new_callable=AsyncMock,
            ) as mock_get_users,
            patch(
                "app.api.v1.endpoints.admin.count_total_users", new_callable=AsyncMock
            ) as mock_count_users,
        ):
            mock_get_users.return_value = mock_users
            mock_count_users.return_value = 2

            response = admin_authenticated_client.get("/api/v1/admin/users")
            assert response.status_code == 200

            data = response.json()
            assert "users" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert data["total"] == 2
            assert data["limit"] == 100
            assert data["offset"] == 0

    def test_list_users_with_pagination(self, admin_authenticated_client: TestClient):
        """Test user listing with pagination parameters."""
        admin_user = create_mock_user(MockUserData.get_admin_user())
        mock_users = [admin_user]

        with (
            patch(
                "app.api.v1.endpoints.admin.get_users_with_roles",
                new_callable=AsyncMock,
            ) as mock_get_users,
            patch(
                "app.api.v1.endpoints.admin.count_total_users", new_callable=AsyncMock
            ) as mock_count_users,
        ):
            mock_get_users.return_value = mock_users
            mock_count_users.return_value = 100

            response = admin_authenticated_client.get(
                "/api/v1/admin/users?limit=50&offset=10"
            )
            assert response.status_code == 200

            data = response.json()
            assert data["limit"] == 50
            assert data["offset"] == 10

            # Verify service was called with correct parameters
            mock_get_users.assert_called_once()
            call_args = mock_get_users.call_args
            # Check positional args: db, limit, offset
            assert call_args[0][1] == 50  # limit is 2nd positional arg
            assert call_args[0][2] == 10  # offset is 3rd positional arg

    def test_list_users_with_email_filter(self, admin_authenticated_client: TestClient):
        """Test user listing with email filter."""
        admin_user = create_mock_user(MockUserData.get_admin_user())
        mock_users = [admin_user]

        with (
            patch(
                "app.api.v1.endpoints.admin.search_users_by_email",
                new_callable=AsyncMock,
            ) as mock_search,
            patch(
                "app.api.v1.endpoints.admin.count_users_by_email",
                new_callable=AsyncMock,
            ) as mock_count_by_email,
        ):
            mock_search.return_value = mock_users
            mock_count_by_email.return_value = 1

            response = admin_authenticated_client.get("/api/v1/admin/users?email=admin")
            assert response.status_code == 200

            # Verify search was called instead of get_users_with_roles
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            # Check positional args: db, email_pattern, limit
            assert call_args[0][1] == "admin"  # email_pattern is 2nd positional arg
            assert call_args[0][2] == 100  # limit is 3rd positional arg

    def test_get_user_requires_admin(self, client: TestClient):
        """Test that GET /admin/users/{id} requires admin role."""
        response = client.get("/api/v1/admin/users/1")
        assert response.status_code == 401

    def test_get_user_success(self, admin_authenticated_client: TestClient):
        """Test successful user retrieval."""
        # Create proper User model instance
        mock_user = create_mock_user(MockUserData.get_default_user())

        with patch("app.repositories.user.UserRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo.get_by_id_with_role = AsyncMock(return_value=mock_user)
            mock_repo_class.return_value = mock_repo

            response = admin_authenticated_client.get("/api/v1/admin/users/1")
            assert response.status_code == 200

            # Verify repository was called with correct user ID
            mock_repo.get_by_id_with_role.assert_called_once()
            call_args = mock_repo.get_by_id_with_role.call_args
            # Check positional args: db, user_id
            assert call_args[0][1] == 1  # user_id is 2nd positional arg

    def test_get_user_not_found(self, admin_authenticated_client: TestClient):
        """Test user retrieval when user doesn't exist."""
        with patch("app.repositories.user.UserRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo.get_by_id_with_role = AsyncMock(return_value=None)
            mock_repo_class.return_value = mock_repo

            response = admin_authenticated_client.get("/api/v1/admin/users/999")
            assert response.status_code == 404
            assert "User with ID 999 not found" in response.json()["detail"]

    def test_update_user_role_requires_admin(self, client: TestClient):
        """Test that PUT /admin/users/{id}/role requires admin role."""
        response = client.put("/api/v1/admin/users/1/role", json={"role_name": "admin"})
        assert response.status_code == 401

    def test_update_user_role_self_protection(
        self, admin_authenticated_client: TestClient
    ):
        """Test that admin cannot change their own role."""
        # The admin_authenticated_client uses mock admin with ID 2
        with (
            patch("app.api.v1.endpoints.admin.get_role_service") as mock_get_service,
        ):
            mock_service = Mock()
            mock_role = Role(id=1, name="user", description="Standard User")
            mock_service.get_role_by_name = AsyncMock(return_value=mock_role)
            mock_get_service.return_value = mock_service

            response = admin_authenticated_client.put(
                "/api/v1/admin/users/2/role",  # Same ID as mock admin user
                json={"role_name": "user"},
            )
            assert response.status_code == 400
            assert "Cannot modify your own role" in response.json()["detail"]

    def test_update_user_role_invalid_role(
        self, admin_authenticated_client: TestClient
    ):
        """Test role update with non-existent role."""
        with patch(
            "app.api.v1.endpoints.admin.assign_user_role", new_callable=AsyncMock
        ) as mock_assign:
            # Mock assign_user_role to raise ValueError for invalid role
            mock_assign.side_effect = ValueError("Role 'nonexistent' not found")

            response = admin_authenticated_client.put(
                "/api/v1/admin/users/1/role",  # Different from admin ID
                json={"role_name": "nonexistent"},
            )

            # Verify the service was called
            mock_assign.assert_called_once()

            # Should get 400 for invalid role
            assert response.status_code == 400
            assert "Role 'nonexistent' not found" in response.json()["detail"]

    def test_update_user_role_success(self, admin_authenticated_client: TestClient):
        """Test successful user role update."""
        # Create proper User model instance with admin role
        updated_user_data = MockUserData.get_default_user()
        updated_user_data["role"] = Role(
            id=1, name="admin", description="Administrator"
        )
        updated_user_data["role_id"] = 1
        mock_updated_user = create_mock_user(updated_user_data)

        with (
            patch("app.api.v1.endpoints.admin.get_role_service") as mock_get_service,
            patch(
                "app.api.v1.endpoints.admin.assign_user_role", new_callable=AsyncMock
            ) as mock_assign,
        ):
            mock_service = Mock()
            mock_role = Role(id=1, name="admin", description="Administrator")
            mock_service.get_role_by_name = AsyncMock(return_value=mock_role)
            mock_get_service.return_value = mock_service
            mock_assign.return_value = mock_updated_user

            response = admin_authenticated_client.put(
                "/api/v1/admin/users/1/role",  # Different from admin ID
                json={"role_name": "admin"},
            )
            assert response.status_code == 200

            # Verify assign_user_role was called correctly
            mock_assign.assert_called_once()
            call_args = mock_assign.call_args
            # Check positional args: db, user_id, role_name
            assert call_args[0][1] == 1  # user_id is 2nd positional arg
            assert call_args[0][2] == "admin"  # role_name is 3rd positional arg

    def test_update_user_role_user_not_found(
        self, admin_authenticated_client: TestClient
    ):
        """Test role update when target user doesn't exist."""
        with (
            patch("app.api.v1.endpoints.admin.get_role_service") as mock_get_service,
            patch(
                "app.api.v1.endpoints.admin.assign_user_role", new_callable=AsyncMock
            ) as mock_assign,
        ):
            mock_service = Mock()
            mock_role = Role(id=1, name="admin", description="Administrator")
            mock_service.get_role_by_name = AsyncMock(return_value=mock_role)
            mock_get_service.return_value = mock_service
            mock_assign.return_value = None  # User not found

            response = admin_authenticated_client.put(
                "/api/v1/admin/users/999/role", json={"role_name": "admin"}
            )
            assert response.status_code == 404
            assert "User with ID 999 not found" in response.json()["detail"]

    def test_update_user_role_logs_admin_action(
        self, admin_authenticated_client: TestClient
    ):
        """Test that role updates log admin actions."""
        # Create proper User model instance
        mock_updated_user = create_mock_user(MockUserData.get_default_user())

        with (
            patch("app.api.v1.endpoints.admin.get_role_service") as mock_get_service,
            patch(
                "app.api.v1.endpoints.admin.assign_user_role", new_callable=AsyncMock
            ) as mock_assign,
            patch("app.api.v1.endpoints.admin.logger") as mock_logger,
        ):
            mock_service = Mock()
            mock_role = Role(id=1, name="admin", description="Administrator")
            mock_service.get_role_by_name = AsyncMock(return_value=mock_role)
            mock_get_service.return_value = mock_service
            mock_assign.return_value = mock_updated_user

            response = admin_authenticated_client.put(
                "/api/v1/admin/users/1/role", json={"role_name": "admin"}
            )
            assert response.status_code == 200

            # Verify admin action was logged
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "Admin" in log_message
            assert "updated user 1 role to admin" in log_message


class TestAdminEndpointSchemas:
    """Test admin endpoint request/response schemas."""

    def test_user_role_update_schema_validation(
        self, admin_authenticated_client: TestClient
    ):
        """Test UserRoleUpdate schema validation."""
        # Test missing role_name
        response = admin_authenticated_client.put("/api/v1/admin/users/1/role", json={})
        assert response.status_code == 422

        # Test empty role_name
        response = admin_authenticated_client.put(
            "/api/v1/admin/users/1/role", json={"role_name": ""}
        )
        assert response.status_code == 422

        # Test role_name too long
        response = admin_authenticated_client.put(
            "/api/v1/admin/users/1/role",
            json={"role_name": "a" * 51},  # Max length is 50
        )
        assert response.status_code == 422

    def test_list_users_query_params_validation(
        self, admin_authenticated_client: TestClient
    ):
        """Test query parameter validation for list users endpoint."""
        # Test negative limit
        response = admin_authenticated_client.get("/api/v1/admin/users?limit=-1")
        assert response.status_code == 422

        # Test limit too large
        response = admin_authenticated_client.get("/api/v1/admin/users?limit=1001")
        assert response.status_code == 422

        # Test negative offset
        response = admin_authenticated_client.get("/api/v1/admin/users?offset=-1")
        assert response.status_code == 422
