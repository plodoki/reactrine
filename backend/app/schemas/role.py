"""Pydantic schemas for role-related API operations."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """Base role schema with common fields."""

    name: str = Field(..., min_length=1, max_length=50, description="Role name")
    description: Optional[str] = Field(
        None, max_length=255, description="Role description"
    )

    class Config:
        from_attributes = True


class RoleCreate(RoleBase):
    """Schema for creating a new role."""

    pass


class Role(RoleBase):
    """Schema for role responses."""

    id: int = Field(..., description="Role ID")
    created_at: datetime = Field(..., description="Role creation timestamp")
    updated_at: datetime = Field(..., description="Role last update timestamp")

    class Config:
        from_attributes = True


class RoleList(BaseModel):
    """Schema for role list responses."""

    roles: List[Role] = Field(..., description="List of roles")
    total: int = Field(..., description="Total number of roles")


class UserRoleUpdate(BaseModel):
    """Schema for updating a user's role."""

    role_name: str = Field(
        ..., min_length=1, max_length=50, description="Role name to assign to user"
    )

    class Config:
        json_schema_extra = {"example": {"role_name": "admin"}}


class UserWithRole(BaseModel):
    """Schema for user with role information."""

    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    auth_provider: str = Field(..., description="Authentication provider")
    is_active: bool = Field(..., description="User active status")
    role: Optional[RoleBase] = Field(None, description="User role")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")

    class Config:
        from_attributes = True


class UserList(BaseModel):
    """Schema for user list responses."""

    users: List[UserWithRole] = Field(..., description="List of users with roles")
    total: int = Field(..., description="Total number of users")
    limit: int = Field(..., description="Number of users per page")
    offset: int = Field(..., description="Number of users skipped")
