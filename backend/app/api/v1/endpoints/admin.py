"""Admin API endpoints for user and role management."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rbac import AdminOnly
from app.core.logging import get_logger
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.role import Role, RoleList, UserList, UserRoleUpdate, UserWithRole
from app.schemas.user import UserDeletionResponse, UserStatusUpdate
from app.services.role import RoleService, get_role_service
from app.services.user import (
    assign_user_role,
    count_total_users,
    count_users_by_email,
    delete_user,
    disable_user,
    enable_user,
    get_users_with_roles,
    search_users_by_email,
)

router = APIRouter()
logger = get_logger(__name__)


@router.get("/roles", response_model=RoleList, tags=["admin"])
async def list_roles(
    current_user: User = Depends(AdminOnly),
    db: AsyncSession = Depends(get_db_session),
    role_service: RoleService = Depends(get_role_service),
) -> RoleList:
    """
    List all available roles.

    Requires admin privileges.
    """
    role_models = await role_service.get_all_roles(db)
    roles = [Role.model_validate(role) for role in role_models]
    return RoleList(roles=roles, total=len(roles))


@router.get("/users", response_model=UserList, tags=["admin"])
async def list_users(
    current_user: User = Depends(AdminOnly),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    email: Optional[str] = Query(None, description="Filter by email pattern"),
) -> UserList:
    """
    List users with their roles.

    Supports pagination and email filtering.
    Requires admin privileges.
    """
    if email:
        users = await search_users_by_email(db, email, limit)
        total = await count_users_by_email(db, email)
    else:
        users = await get_users_with_roles(db, limit, offset)
        total = await count_total_users(db)

    user_schemas = [UserWithRole.model_validate(user) for user in users]
    return UserList(
        users=user_schemas,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/users/{user_id}", response_model=UserWithRole, tags=["admin"])
async def get_user(
    user_id: int,
    current_user: User = Depends(AdminOnly),
    db: AsyncSession = Depends(get_db_session),
) -> UserWithRole:
    """
    Get a specific user with role information.

    Requires admin privileges.
    """
    from app.repositories.user import UserRepository

    user_repo = UserRepository()
    user = await user_repo.get_by_id_with_role(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    return UserWithRole.model_validate(user)


@router.put("/users/{user_id}/role", response_model=UserWithRole, tags=["admin"])
async def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    current_user: User = Depends(AdminOnly),
    db: AsyncSession = Depends(get_db_session),
    role_service: RoleService = Depends(get_role_service),
) -> UserWithRole:
    """
    Update a user's role.

    Requires admin privileges.
    Cannot modify own role (self-protection).
    """
    # Self-protection: prevent admin from changing their own role
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own role",
        )

    # Validate role exists
    role = await role_service.get_role_by_name(db, role_update.role_name)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_update.role_name}' not found",
        )

    # Update user role
    try:
        updated_user = await assign_user_role(db, user_id, role_update.role_name)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        logger.info(
            f"Admin {current_user.email} updated user {user_id} role to {role_update.role_name}",
            extra={
                "admin_id": current_user.id,
                "target_user_id": user_id,
                "new_role": role_update.role_name,
            },
        )

        return UserWithRole.model_validate(updated_user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/users/{user_id}/status", response_model=UserWithRole, tags=["admin"])
async def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    current_user: User = Depends(AdminOnly),
    db: AsyncSession = Depends(get_db_session),
) -> UserWithRole:
    """
    Enable or disable a user account.

    Requires admin privileges.
    Cannot modify own status (self-protection).
    """
    # Self-protection: prevent admin from disabling themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own account status",
        )

    # Update user status
    try:
        if status_update.is_active:
            updated_user = await enable_user(db, user_id)
            action = "enabled"
        else:
            updated_user = await disable_user(db, user_id)
            action = "disabled"

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        logger.info(
            f"Admin {current_user.email} {action} user {user_id}",
            extra={
                "admin_id": current_user.id,
                "target_user_id": user_id,
                "action": action,
            },
        )

        return UserWithRole.model_validate(updated_user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/users/{user_id}", response_model=UserDeletionResponse, tags=["admin"])
async def delete_user_account(
    user_id: int,
    current_user: User = Depends(AdminOnly),
    db: AsyncSession = Depends(get_db_session),
) -> UserDeletionResponse:
    """
    Permanently delete a user account.

    Requires admin privileges.
    Cannot delete own account (self-protection).
    This action cannot be undone.
    """
    # Self-protection: prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Delete user
    try:
        deletion_successful = await delete_user(db, user_id)

        if not deletion_successful:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        logger.warning(
            f"Admin {current_user.email} permanently deleted user {user_id}",
            extra={
                "admin_id": current_user.id,
                "target_user_id": user_id,
                "action": "permanent_deletion",
            },
        )

        return UserDeletionResponse(
            success=True,
            message="User successfully deleted",
            user_id=user_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
