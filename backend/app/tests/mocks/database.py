"""
Database mock utilities for testing.

This module provides reusable database mocking patterns that avoid global state
and ensure proper test isolation.
"""

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type
from unittest.mock import AsyncMock

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role


class MockDatabase:
    """
    Mock database that provides isolated storage per test instance.

    This replaces the global _mock_data pattern with proper test isolation.
    """

    def __init__(self) -> None:
        """Initialize empty mock database with default roles."""
        self._data: Dict[str, Any] = {}
        self._pending_objects: list[tuple[str, Any]] = []
        self._initialize_default_roles()

    def _initialize_default_roles(self) -> None:
        """Initialize default roles in the mock database."""
        # Create admin role
        admin_role = Role(
            id=1,
            name="admin",
            description="Administrator",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._data[self._get_model_key(Role, 1)] = admin_role

        # Create user role
        user_role = Role(
            id=2,
            name="user",
            description="Standard User",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._data[self._get_model_key(Role, 2)] = user_role

    def _get_model_key(self, model_class: Type, id_value: Any) -> str:
        """Generate a unique key for storing model instances."""
        return f"{model_class.__name__}_{id_value}"

    def get(self, model_class: Type, id_value: Any) -> Optional[Any]:
        """Mock the db.get() method."""
        model_key = self._get_model_key(model_class, id_value)
        return self._data.get(model_key)

    def add(self, obj: Any) -> None:
        """Mock the db.add() method."""
        if not hasattr(obj, "__class__"):
            return

        try:
            # Extract the actual id from the object
            obj_id = getattr(obj, "id", None)

            # Handle cases where id is None or invalid
            if obj_id is None:
                # Generate a simple incremental id if none exists
                existing_keys = [
                    k
                    for k in self._data.keys()
                    if k.startswith(f"{obj.__class__.__name__}_")
                ]
                obj_id = len(existing_keys) + 1
                # Set the id on the object for consistency
                obj.id = obj_id

            # Create the key using the actual id
            model_key = self._get_model_key(obj.__class__, obj_id)

            # Store as pending for commit
            self._pending_objects.append((model_key, obj))

        except (AttributeError, TypeError):
            # Silently ignore objects that can't be processed
            pass

    async def execute(self, statement):
        """Mock execute to support select queries with WHERE clauses."""
        try:
            # Import model classes - extend this list as you add new models
            from app.models.api_key import ApiKey
            from app.models.role import Role
            from app.models.user import User

            # Add new model imports here as you extend the system
            # Example: from app.models.blog_post import BlogPost
            # from app.models.comment import Comment
            # Check if this is a SELECT statement by looking at the type name
            if hasattr(statement, "__class__") and "Select" in str(type(statement)):
                # Parse the SQL query directly since SelectOfScalar doesn't have table attribute
                sql_str = str(statement)

                # Handle COUNT queries specially
                if "count(" in sql_str.lower():
                    return self._handle_count_query(sql_str, statement)

                # Handle queries by table name - extend this for new models
                model_handlers = {
                    ("apikey", "api_keys"): (ApiKey, self._handle_api_key_query),
                    ("users", "user"): (User, self._handle_user_query),
                    ("roles", "role"): (Role, self._handle_role_query),
                    # Example: Add new models here:
                    # ("blog_posts", "blogpost"): (BlogPost, self._handle_blog_post_query),
                    # ("comments", "comment"): (Comment, self._handle_comment_query),
                }

                # Find matching handler
                for table_names, (model_class, handler) in model_handlers.items():
                    if any(f"FROM {table}" in sql_str for table in table_names):
                        return handler(sql_str, statement, model_class)

                # Handle other SELECT queries - return all objects
                all_objects = list(self._data.values())
                return self._create_mock_result(all_objects)

        except Exception:
            # Ignore parsing errors and fall through to empty result
            pass

        # Default: return empty result
        return self._create_empty_result()

    def _handle_api_key_query(self, sql_str: str, statement, model_class):
        """Handle ApiKey-specific queries."""
        # Filter ApiKey objects from stored data
        api_keys = [obj for obj in self._data.values() if isinstance(obj, model_class)]

        # Parse WHERE clause for user_id filter
        if "user_id" in sql_str and "=" in sql_str:
            try:
                # Extract user_id value from parameterized query
                if hasattr(statement, "compile"):
                    compiled = statement.compile(compile_kwargs={"literal_binds": True})
                    compiled_str = str(compiled)

                    # Extract user_id from compiled query
                    import re

                    match = re.search(r"user_id\s*=\s*(\d+)", compiled_str)
                    if match:
                        user_id = int(match.group(1))
                        # Filter by user_id
                        api_keys = [key for key in api_keys if key.user_id == user_id]
            except Exception:
                # If parsing fails, return all api_keys
                pass

        return self._create_mock_result(api_keys)

    def _handle_user_query(self, sql_str: str, statement, model_class):
        """Handle User-specific queries."""
        # Filter User objects from stored data
        users = [obj for obj in self._data.values() if isinstance(obj, model_class)]

        # Add WHERE clause parsing for users if needed
        # Example: Parse email filter
        # if "email" in sql_str and "=" in sql_str:
        #     try:
        #         if hasattr(statement, "compile"):
        #             compiled = statement.compile(compile_kwargs={"literal_binds": True})
        #             compiled_str = str(compiled)
        #
        #             import re
        #             match = re.search(r"email\s*=\s*['\"]([^'\"]+)['\"]", compiled_str)
        #             if match:
        #                 email = match.group(1)
        #                 users = [user for user in users if user.email == email]
        #     except Exception:
        #         pass

        return self._create_mock_result(users)

    def _handle_role_query(self, sql_str: str, statement, model_class):
        """Handle Role-specific queries."""
        # Filter Role objects from stored data
        roles = [obj for obj in self._data.values() if isinstance(obj, model_class)]

        # Add WHERE clause parsing for roles if needed
        # Example: Parse name filter
        if "name" in sql_str and "=" in sql_str:
            try:
                if hasattr(statement, "compile"):
                    compiled = statement.compile(compile_kwargs={"literal_binds": True})
                    compiled_str = str(compiled)

                    import re

                    match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", compiled_str)
                    if match:
                        name = match.group(1)
                        roles = [role for role in roles if role.name == name]
            except Exception:
                pass

        return self._create_mock_result(roles)

    # Example: Handler for a new BlogPost model
    # def _handle_blog_post_query(self, sql_str: str, statement, model_class):
    #     """Handle BlogPost-specific queries."""
    #     # Filter BlogPost objects from stored data
    #     posts = [obj for obj in self._data.values() if isinstance(obj, model_class)]
    #
    #     # Parse WHERE clause for author_id filter
    #     if "author_id" in sql_str and "=" in sql_str:
    #         try:
    #             if hasattr(statement, "compile"):
    #                 compiled = statement.compile(compile_kwargs={"literal_binds": True})
    #                 compiled_str = str(compiled)
    #
    #                 import re
    #                 match = re.search(r"author_id\s*=\s*(\d+)", compiled_str)
    #                 if match:
    #                     author_id = int(match.group(1))
    #                     posts = [post for post in posts if post.author_id == author_id]
    #         except Exception:
    #             pass
    #
    #     # Parse WHERE clause for published status
    #     if "published" in sql_str and ("= true" in sql_str or "= false" in sql_str):
    #         try:
    #             published = "= true" in sql_str.lower()
    #             posts = [post for post in posts if post.published == published]
    #         except Exception:
    #             pass
    #
    #     return self._create_mock_result(posts)

    def _handle_count_query(self, sql_str: str, statement):
        """Handle COUNT queries and return appropriate count."""
        try:
            from app.models.api_key import ApiKey
            from app.models.role import Role
            from app.models.user import User

            # Determine which table is being counted
            count = 0
            if any(table in sql_str.lower() for table in ["user", "users"]):
                users = [obj for obj in self._data.values() if isinstance(obj, User)]

                # Handle email filtering for count
                if "ilike" in sql_str.lower() and "email" in sql_str.lower():
                    # Extract email pattern (simplified - you can improve this)
                    # For now, just return the count of all users
                    count = len(users)
                else:
                    count = len(users)
            elif any(table in sql_str.lower() for table in ["apikey", "api_keys"]):
                api_keys = [
                    obj for obj in self._data.values() if isinstance(obj, ApiKey)
                ]
                count = len(api_keys)
            elif any(table in sql_str.lower() for table in ["role", "roles"]):
                roles = [obj for obj in self._data.values() if isinstance(obj, Role)]
                count = len(roles)

            return self._create_count_result(count)
        except Exception:
            return self._create_count_result(0)

    def _create_count_result(self, count: int):
        """Create a mock result for count queries."""

        class MockCountResult:
            def scalar(self):
                return count

            def scalars(self):
                class MockScalars:
                    def first(self):
                        return count

                    def all(self):
                        return [count]

                return MockScalars()

        return MockCountResult()

    def _create_mock_result(self, objects: list):
        """Create a mock result object with the given objects."""

        class MockResult:
            def scalars(self):
                class MockScalars:
                    def first(self):
                        return objects[0] if objects else None

                    def all(self):
                        return objects

                return MockScalars()

        return MockResult()

    def _create_empty_result(self):
        """Create an empty mock result."""

        class MockEmptyResult:
            def scalars(self):
                class MockEmptyScalars:
                    def first(self):
                        return None

                    def all(self):
                        return []

                return MockEmptyScalars()

        return MockEmptyResult()

    async def commit(self) -> None:
        """Mock the db.commit() method with constraint checking."""
        for model_key, obj in self._pending_objects:
            # Check for duplicate primary key
            if model_key in self._data:
                # Clear pending objects on error
                self._pending_objects = []
                # Create a simple IntegrityError - ignore linter error as this matches existing tests
                error = IntegrityError(
                    "duplicate key value violates unique constraint",
                    None,
                    None,  # type: ignore
                )
                raise error
            # If no conflict, add to data
            self._data[model_key] = obj

        # Clear pending objects after successful commit
        self._pending_objects = []

    async def rollback(self) -> None:
        """Mock the db.rollback() method."""
        self._pending_objects = []

    async def merge(self, obj: Any) -> Any:
        """Mock the db.merge() method."""
        # In real implementation, this would merge the object into the session
        # For mocking, we just return the object as-is since it's already in memory
        return obj

    def refresh(self, obj: Any) -> None:
        """Mock the db.refresh() method."""
        # In real implementation, this would reload from database
        # For mocking, we just leave the object as-is
        pass

    def close(self) -> None:
        """Mock the db.close() method."""
        pass

    def clear(self) -> None:
        """Clear all data - useful for test cleanup."""
        self._data.clear()
        self._pending_objects.clear()


# Global reference to the current test's mock database
_current_mock_db: Optional[MockDatabase] = None


def create_test_mock_db() -> MockDatabase:
    """
    Create a new mock database for a test.

    This should be called at the start of each test to ensure isolation.
    """
    global _current_mock_db
    _current_mock_db = MockDatabase()
    return _current_mock_db


def get_current_mock_db() -> MockDatabase:
    """
    Get the current test's mock database.

    This is used by the dependency override to ensure all requests
    in the same test use the same mock database instance.
    """
    global _current_mock_db
    if _current_mock_db is None:
        _current_mock_db = MockDatabase()
    return _current_mock_db


def clear_test_mock_db() -> None:
    """
    Clear the current test's mock database.

    This should be called at the end of each test for cleanup.
    """
    global _current_mock_db
    if _current_mock_db is not None:
        _current_mock_db.clear()
        _current_mock_db = None


async def create_mock_db_session() -> AsyncGenerator[AsyncMock, None]:
    """
    Create a mock database session with proper isolation.

    This replaces the global state pattern with per-test isolation.
    """
    mock_db = MockDatabase()
    mock_session = AsyncMock(spec=AsyncSession)

    # Wire up the mock methods
    mock_session.get.side_effect = mock_db.get
    mock_session.add.side_effect = mock_db.add
    mock_session.execute.side_effect = mock_db.execute
    mock_session.commit.side_effect = mock_db.commit
    mock_session.rollback.side_effect = mock_db.rollback
    mock_session.merge.side_effect = mock_db.merge
    mock_session.refresh.side_effect = mock_db.refresh
    mock_session.close.side_effect = mock_db.close

    # Store reference to mock_db for test access if needed
    mock_session._mock_db = mock_db

    yield mock_session


async def create_persistent_mock_db_session() -> AsyncGenerator[AsyncMock, None]:
    """
    Create a mock database session that persists across requests in the same test.

    This uses the global mock database instance to ensure data persistence
    between HTTP requests in integration tests.
    """
    mock_db = get_current_mock_db()
    mock_session = AsyncMock(spec=AsyncSession)

    # Wire up the mock methods
    mock_session.get.side_effect = mock_db.get
    mock_session.add.side_effect = mock_db.add
    mock_session.execute.side_effect = mock_db.execute
    mock_session.commit.side_effect = mock_db.commit
    mock_session.rollback.side_effect = mock_db.rollback
    mock_session.merge.side_effect = mock_db.merge
    mock_session.refresh.side_effect = mock_db.refresh
    mock_session.close.side_effect = mock_db.close

    # Store reference to mock_db for test access if needed
    mock_session._mock_db = mock_db

    yield mock_session


def create_simple_mock_db_session() -> AsyncMock:
    """
    Create a simple mock database session for basic testing.

    Use this when you don't need complex database behavior simulation.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.get.return_value = None
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    mock_session.refresh.return_value = None
    mock_session.close.return_value = None

    return mock_session
