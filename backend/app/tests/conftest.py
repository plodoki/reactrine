"""
Pytest configuration and shared fixtures for backend tests.

This module provides common fixtures that can be used across all test modules,
including test client, database session, and authentication mocks.
"""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.deps import get_current_active_user, get_current_user
from app.db.session import get_db_session
from app.main import app

from .mocks import (
    clear_test_mock_db,
    create_mock_current_admin_user,
    create_mock_current_user,
    create_mock_db_session,
    create_mock_user_dict,
    create_persistent_mock_db_session,
    create_test_mock_db,
)

# Configure pytest-asyncio - moved to pyproject.toml


async def mock_get_current_user():
    """Mock current user for testing."""
    return create_mock_current_user()


async def mock_get_current_active_user():
    """Mock current active user for testing."""
    return create_mock_current_user()


async def mock_get_current_admin_user():
    """Mock current admin user for testing."""
    return create_mock_current_admin_user()


async def mock_get_current_active_admin_user():
    """Mock current active admin user for testing."""
    return create_mock_current_admin_user()


async def mock_get_user_by_email_with_role(db, email: str):
    """Mock get_user_by_email_with_role for testing."""
    # Return regular user by default
    user = create_mock_current_user()
    # Ensure the user has the expected structure
    if not hasattr(user, "role") or user.role is None:
        raise ValueError(f"Mock user missing role: {user}")
    if not hasattr(user.role, "name"):
        raise ValueError(f"Mock user role missing name: {user.role}")
    return user


async def mock_get_admin_user_by_email_with_role(db, email: str):
    """Mock get_user_by_email_with_role for admin testing."""
    # Return admin user
    user = create_mock_current_admin_user()
    # Ensure the user has the expected structure
    if not hasattr(user, "role") or user.role is None:
        raise ValueError(f"Mock admin user missing role: {user}")
    if not hasattr(user.role, "name"):
        raise ValueError(f"Mock admin user role missing name: {user.role}")
    return user


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    yield


@pytest.fixture(autouse=True)
def setup_mock_database():
    """Set up and clean up mock database for each test."""
    # Create a fresh mock database for this test
    create_test_mock_db()
    yield
    # Clean up after test
    clear_test_mock_db()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create a test client for the FastAPI application.
    This client uses persistent mock database for integration tests.

    Yields:
        TestClient: A test client instance for making HTTP requests.
    """
    # Mock database initialization to prevent actual database connections
    with (
        patch("app.db.init_db.init_database") as mock_init_db,
        patch("app.core.config.settings.ENVIRONMENT", "test"),
    ):
        mock_init_db.return_value = None

        # Set up database override for this client - use persistent session
        app.dependency_overrides[get_db_session] = create_persistent_mock_db_session

        with TestClient(app) as test_client:
            yield test_client

        # Clean up after test
        app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client() -> Generator[TestClient, None, None]:
    """
    Create a test client with authentication mocked.
    This client uses persistent mock database for integration tests.

    Yields:
        TestClient: A test client instance with authentication overrides.
    """
    # Mock database initialization to prevent actual database connections
    with (
        patch("app.db.init_db.init_database") as mock_init_db,
        patch("app.core.config.settings.ENVIRONMENT", "test"),
        # Patch get_user_by_email_with_role where it's used (in RBAC module)
        patch(
            "app.api.rbac.get_user_by_email_with_role",
            side_effect=mock_get_user_by_email_with_role,
        ),
    ):
        mock_init_db.return_value = None

        # Set up all necessary overrides for authenticated client
        app.dependency_overrides[get_db_session] = create_persistent_mock_db_session
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_current_active_user] = mock_get_current_active_user

        with TestClient(app) as test_client:
            yield test_client

        # Clean up all overrides after test
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for the FastAPI application.

    Yields:
        AsyncClient: An async test client instance for making HTTP requests.
    """
    from httpx import ASGITransport

    # Set up database override - use persistent session for async client too
    app.dependency_overrides[get_db_session] = create_persistent_mock_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    # Clean up after test
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def mock_db_session():
    """
    Create a mock database session for testing.

    Returns:
        AsyncMock: A mock database session that avoids real database connections.
    """
    async for session in create_mock_db_session():
        yield session


@pytest.fixture
def mock_user():
    """
    Create a mock user for testing authentication.

    Returns:
        dict: A mock user object with basic user information.
    """
    return create_mock_user_dict()


@pytest.fixture
def auth_headers():
    """
    Create authentication headers for testing protected endpoints.
    NOTE: These headers should be used with authenticated_client, not regular client.

    Returns:
        dict: Headers with a mock JWT token.
    """
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def superuser_headers():
    """
    Create superuser authentication headers for testing admin endpoints.
    NOTE: These headers should be used with authenticated_client, not regular client.

    Returns:
        dict: Headers with a mock superuser JWT token.
    """
    return {"Authorization": "Bearer superuser-token"}


@pytest.fixture
def admin_authenticated_client() -> Generator[TestClient, None, None]:
    """
    Create a test client with admin authentication mocked.
    This client uses persistent mock database for integration tests.

    Yields:
        TestClient: A test client instance with admin authentication overrides.
    """
    # Mock database initialization to prevent actual database connections
    with (
        patch("app.db.init_db.init_database") as mock_init_db,
        patch("app.core.config.settings.ENVIRONMENT", "test"),
        # Patch get_user_by_email_with_role where it's used (in RBAC module)
        patch(
            "app.api.rbac.get_user_by_email_with_role",
            side_effect=mock_get_admin_user_by_email_with_role,
        ),
    ):
        mock_init_db.return_value = None

        # Set up all necessary overrides for admin authenticated client
        app.dependency_overrides[get_db_session] = create_persistent_mock_db_session
        app.dependency_overrides[get_current_user] = mock_get_current_admin_user
        app.dependency_overrides[get_current_active_user] = (
            mock_get_current_active_admin_user
        )

        with TestClient(app) as test_client:
            yield test_client

        # Clean up all overrides after test
        app.dependency_overrides.clear()
