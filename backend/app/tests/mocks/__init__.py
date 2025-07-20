"""
Mock utilities for testing.

This module provides reusable mock utilities and patterns for consistent testing
across the application.
"""

from .database import (
    MockDatabase,
    clear_test_mock_db,
    create_mock_db_session,
    create_persistent_mock_db_session,
    create_test_mock_db,
    get_current_mock_db,
)
from .users import (
    MockUserData,
    create_mock_current_admin_user,
    create_mock_current_user,
    create_mock_user,
    create_mock_user_dict,
)

__all__ = [
    "MockDatabase",
    "create_mock_db_session",
    "create_persistent_mock_db_session",
    "create_test_mock_db",
    "get_current_mock_db",
    "clear_test_mock_db",
    "create_mock_user",
    "create_mock_user_dict",
    "create_mock_current_user",
    "create_mock_current_admin_user",
    "MockUserData",
]
