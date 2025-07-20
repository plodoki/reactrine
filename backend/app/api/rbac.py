"""Role-based access control dependencies for FastAPI."""

from typing import Awaitable, Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db_session
from app.models.user import User
from app.services.user import get_user_by_email_with_role

logger = get_logger(__name__)


def RoleRequired(*required_roles: str) -> Callable[..., Awaitable[User]]:
    """
    FastAPI dependency factory for role-based access control.

    Args:
        *required_roles: Role names that are allowed to access the endpoint

    Returns:
        FastAPI dependency function that checks user roles

    Example:
        @router.get("/admin/users", dependencies=[Depends(RoleRequired("admin"))])
        async def list_users():
            return {"users": [...]}
    """

    async def check_role(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session),
    ) -> User:
        """
        Check if the current user has one of the required roles.

        Args:
            current_user: Current authenticated user
            db: Database session

        Returns:
            User object if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        # Get user with role loaded
        user_with_role = await get_user_by_email_with_role(db, current_user.email)

        if not user_with_role or not user_with_role.role:
            logger.warning(
                f"User {current_user.email} has no role assigned",
                extra={
                    "user_id": current_user.id,
                    "required_roles": required_roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: No role assigned",
            )

        user_role = user_with_role.role.name.lower()

        # Convert required roles to lowercase for case-insensitive comparison
        required_roles_lower = [role.lower() for role in required_roles]

        if user_role not in required_roles_lower:
            logger.warning(
                f"User {current_user.email} with role '{user_role}' "
                f"attempted to access endpoint requiring roles: {required_roles}",
                extra={
                    "user_id": current_user.id,
                    "user_role": user_role,
                    "required_roles": required_roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Insufficient permissions",
            )

        logger.debug(
            f"User {current_user.email} with role '{user_role}' "
            f"granted access to endpoint requiring roles: {required_roles}",
            extra={
                "user_id": current_user.id,
                "user_role": user_role,
                "required_roles": required_roles,
            },
        )

        result: User = user_with_role
        return result

    return check_role


# Convenient aliases for common role checks
AdminOnly = RoleRequired("admin")
UserOrAdmin = RoleRequired("user", "admin")


def get_user_role(user: User) -> str:
    """
    Helper function to get user role name.

    Args:
        user: User object with role loaded

    Returns:
        Role name

    Raises:
        ValueError: If user has no role
    """
    if not user.role:
        raise ValueError("User has no role assigned")
    return user.role.name


def is_admin(user: User) -> bool:
    """
    Check if user is an admin.

    Args:
        user: User object with role loaded

    Returns:
        True if user is admin, False otherwise
    """
    try:
        return get_user_role(user) == "admin"
    except ValueError:
        return False


def has_role(user: User, role_name: str) -> bool:
    """
    Check if user has a specific role.

    Args:
        user: User object with role loaded
        role_name: Role name to check

    Returns:
        True if user has the role, False otherwise
    """
    try:
        return get_user_role(user) == role_name
    except ValueError:
        return False
