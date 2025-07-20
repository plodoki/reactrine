"""
User mock utilities for testing.

This module provides reusable user mocking patterns for consistent testing
across the application.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from unittest.mock import Mock

from app.models.role import Role
from app.models.user import User


class MockUserData:
    """
    Predefined mock user data for testing.
    """

    @staticmethod
    def get_default_user() -> Dict[str, Any]:
        """Get default test user data with user role."""
        user_role = Role(
            id=2,
            name="user",
            description="Standard User",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return {
            "id": 1,
            "email": "test@example.com",
            "is_active": True,
            "is_superuser": False,
            "hashed_password": "hashed_password_123",
            "auth_provider": "email",  # Add auth_provider field
            "role_id": 2,
            "role": user_role,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

    @staticmethod
    def get_admin_user() -> Dict[str, Any]:
        """Get admin test user data with admin role."""
        admin_role = Role(
            id=1,
            name="admin",
            description="Administrator",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return {
            "id": 2,
            "email": "admin@example.com",
            "is_active": True,
            "is_superuser": True,
            "hashed_password": "hashed_password_admin",
            "auth_provider": "email",  # Add auth_provider field
            "role_id": 1,
            "role": admin_role,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

    @staticmethod
    def get_inactive_user() -> Dict[str, Any]:
        """Get inactive test user data with user role."""
        user_role = Role(
            id=2,
            name="user",
            description="Standard User",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return {
            "id": 3,
            "email": "inactive@example.com",
            "is_active": False,
            "is_superuser": False,
            "hashed_password": "hashed_password_inactive",
            "auth_provider": "email",  # Add auth_provider field
            "role_id": 2,
            "role": user_role,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }


def create_mock_user(user_data: Optional[Dict[str, Any]] = None) -> User:
    """
    Create a mock User object with the given data.

    Args:
        user_data: Dictionary of user attributes. If None, uses default user data.

    Returns:
        User: Mock User object with the specified attributes.
    """
    if user_data is None:
        user_data = MockUserData.get_default_user()

    user = User(**user_data)
    return user


def create_mock_user_dict(user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a mock user dictionary for testing authentication.

    Args:
        user_data: Dictionary of user attributes. If None, uses default user data.

    Returns:
        Dict[str, Any]: Dictionary representation of user for authentication mocks.
    """
    if user_data is None:
        user_data = MockUserData.get_default_user()

    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "is_active": user_data["is_active"],
        "is_superuser": user_data["is_superuser"],
        "auth_provider": user_data["auth_provider"],
        "role_id": user_data["role_id"],
        "role": user_data["role"],
        "created_at": user_data["created_at"],
        "updated_at": user_data["updated_at"],
    }


def create_mock_current_user() -> Mock:
    """
    Create a mock for dependency injection of current user with user role.

    Returns:
        Mock: Mock object that can be used with Depends(get_current_user).
    """
    mock_user = Mock()
    default_data = MockUserData.get_default_user()

    mock_user.id = default_data["id"]
    mock_user.email = default_data["email"]
    mock_user.is_active = default_data["is_active"]
    mock_user.is_superuser = default_data["is_superuser"]
    mock_user.auth_provider = default_data["auth_provider"]  # Add auth_provider
    mock_user.role_id = default_data["role_id"]
    mock_user.role = default_data["role"]
    mock_user.created_at = default_data["created_at"]  # Add created_at
    mock_user.updated_at = default_data["updated_at"]  # Add updated_at

    return mock_user


def create_mock_current_admin_user() -> Mock:
    """
    Create a mock admin user for dependency injection with admin role.

    Returns:
        Mock: Mock admin user object.
    """
    mock_user = Mock()
    admin_data = MockUserData.get_admin_user()

    mock_user.id = admin_data["id"]
    mock_user.email = admin_data["email"]
    mock_user.is_active = admin_data["is_active"]
    mock_user.is_superuser = admin_data["is_superuser"]
    mock_user.auth_provider = admin_data["auth_provider"]  # Add auth_provider
    mock_user.role_id = admin_data["role_id"]
    mock_user.role = admin_data["role"]
    mock_user.created_at = admin_data["created_at"]  # Add created_at
    mock_user.updated_at = admin_data["updated_at"]  # Add updated_at

    return mock_user
