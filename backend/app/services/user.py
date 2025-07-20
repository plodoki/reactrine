from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.security.auth import get_password_hash, verify_password
from app.utils.error_handling import with_database_error_handling


async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
    """
    Create a new user in the database with default role.

    Args:
        db: Database session
        user_create: User creation data

    Returns:
        Created user

    Raises:
        ValueError: If user with email already exists
    """
    from sqlalchemy.exc import IntegrityError

    # Create user
    hashed_password = get_password_hash(user_create.password)
    user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        auth_provider=user_create.auth_provider,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    user_repo = UserRepository()
    role_repo = RoleRepository()

    try:
        # Get default role
        default_role = await role_repo.get_by_name(db, "user")
        if not default_role:
            raise ValueError("Default 'user' role not found")

        # Assign role to user
        user.role_id = default_role.id

        # Create user
        created_user = await user_repo.create(db, user)
        return created_user

    except IntegrityError as e:
        # Check if it's a unique constraint violation on email
        if (
            e.orig is not None
            and getattr(e.orig, "pgcode", None) == "23505"
            and getattr(getattr(e.orig, "diag", None), "constraint_name", None)
            == "ix_user_email"
        ):
            raise ValueError(
                f"User with email {user_create.email} already exists"
            ) from e
        raise


async def create_oauth_user(
    db: AsyncSession, email: str, auth_provider: str = "google"
) -> User:
    """
    Create a new OAuth user in the database without password validation.

    Args:
        db: Database session
        email: User email address
        auth_provider: OAuth provider (e.g., "google")

    Returns:
        Created user

    Raises:
        ValueError: If user with email already exists
    """
    import secrets

    from sqlalchemy.exc import IntegrityError

    # Generate a secure random hash
    secure_random_hash = get_password_hash(secrets.token_urlsafe(64))

    user = User(
        email=email,
        hashed_password=secure_random_hash,
        auth_provider=auth_provider,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    user_repo = UserRepository()
    role_repo = RoleRepository()

    try:
        # Get default role
        default_role = await role_repo.get_by_name(db, "user")
        if not default_role:
            raise ValueError("Default 'user' role not found")

        # Assign role to user
        user.role_id = default_role.id

        # Create user
        created_user = await user_repo.create(db, user)
        return created_user

    except IntegrityError as e:
        if (
            e.orig is not None
            and getattr(e.orig, "pgcode", None) == "23505"
            and getattr(getattr(e.orig, "diag", None), "constraint_name", None)
            == "ix_user_email"
        ):
            raise ValueError(f"User with email {email} already exists") from e
        raise


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by email address.

    Args:
        db: Database session
        email: User email address

    Returns:
        User if found, None otherwise
    """
    user_repo = UserRepository()
    return await user_repo.get_by_email(db, email)


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Get a user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User if found, None otherwise
    """
    user_repo = UserRepository()
    return await user_repo.get_by_id(db, user_id)


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """
    Authenticate a user with email and password.

    Args:
        db: Database session
        email: User email
        password: Plain text password

    Returns:
        User if authentication successful, None otherwise
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None

    # Check if user account is active
    if not user.is_active:
        return None

    # OAuth users cannot login with password
    if user.auth_provider != "email":
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


@with_database_error_handling("get user by email with role")
async def get_user_by_email_with_role(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by email with role loaded.

    Args:
        db: Database session
        email: User email

    Returns:
        User with role if found, None otherwise
    """
    user_repo = UserRepository()
    return await user_repo.get_by_email_with_role(db, email)


@with_database_error_handling("assign user role")
async def assign_user_role(
    db: AsyncSession, user_id: int, role_name: str
) -> Optional[User]:
    """
    Assign a role to a user.

    Args:
        db: Database session
        user_id: User ID
        role_name: Role name to assign

    Returns:
        Updated user if successful, None if user not found

    Raises:
        ValueError: If role not found
    """
    user_repo = UserRepository()
    role_repo = RoleRepository()

    # Get role by name
    role = await role_repo.get_by_name(db, role_name)
    if not role or role.id is None:
        raise ValueError(f"Role '{role_name}' not found")

    # Update user role
    return await user_repo.update_user_role(db, user_id, role.id)


@with_database_error_handling("get users with roles")
async def get_users_with_roles(
    db: AsyncSession, limit: int = 100, offset: int = 0
) -> List[User]:
    """
    Get users with their roles (paginated).

    Args:
        db: Database session
        limit: Maximum number of users to return
        offset: Number of users to skip

    Returns:
        List of users with roles
    """
    user_repo = UserRepository()
    return await user_repo.get_users_with_roles(db, limit, offset)


@with_database_error_handling("search users by email")
async def search_users_by_email(
    db: AsyncSession, email_pattern: str, limit: int = 100
) -> List[User]:
    """
    Search users by email pattern.

    Args:
        db: Database session
        email_pattern: Email pattern to search for
        limit: Maximum number of users to return

    Returns:
        List of users matching the email pattern
    """
    user_repo = UserRepository()
    return await user_repo.search_users_by_email(db, email_pattern, limit)


@with_database_error_handling("count total users")
async def count_total_users(db: AsyncSession) -> int:
    """
    Get the total count of all users.

    Args:
        db: Database session

    Returns:
        Total number of users
    """
    user_repo = UserRepository()
    return await user_repo.count_total_users(db)


@with_database_error_handling("count users by email")
async def count_users_by_email(db: AsyncSession, email_pattern: str) -> int:
    """
    Get the count of users matching an email pattern.

    Args:
        db: Database session
        email_pattern: Email pattern to search for

    Returns:
        Number of users matching the email pattern
    """
    user_repo = UserRepository()
    return await user_repo.count_users_by_email(db, email_pattern)


@with_database_error_handling("disable user")
async def disable_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Disable a user account.

    Args:
        db: Database session
        user_id: User ID to disable

    Returns:
        Updated user if successful, None if user not found
    """
    user_repo = UserRepository()
    return await user_repo.soft_delete_user(db, user_id)


@with_database_error_handling("enable user")
async def enable_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Enable a user account.

    Args:
        db: Database session
        user_id: User ID to enable

    Returns:
        Updated user if successful, None if user not found
    """
    user_repo = UserRepository()
    return await user_repo.activate_user(db, user_id)


@with_database_error_handling("delete user")
async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """
    Permanently delete a user account.

    Args:
        db: Database session
        user_id: User ID to delete

    Returns:
        True if deletion successful, False if user not found

    Raises:
        ValueError: If attempting to delete own account
    """
    user_repo = UserRepository()

    # Get user to check if exists
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        return False

    # Hard delete the user
    return await user_repo.hard_delete_user(db, user_id)
