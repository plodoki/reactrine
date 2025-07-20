import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .role import RoleBase


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User email address")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., description="User password")
    auth_provider: str = Field(default="email", description="Authentication provider")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")

        return v

    @field_validator("auth_provider")
    @classmethod
    def validate_auth_provider(cls, v: str) -> str:
        """Restrict auth_provider to allowed values."""
        allowed_providers = {"email", "google"}
        if v not in allowed_providers:
            raise ValueError(f"auth_provider must be one of: {allowed_providers}")
        return v


class User(UserBase):
    """Schema for user data display (read operations)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    auth_provider: str
    is_active: bool
    role: Optional[RoleBase] = Field(None, description="User role")
    created_at: datetime
    updated_at: datetime


class TokenData(BaseModel):
    """Schema for token payload data."""

    email: Optional[str] = None


class RegistrationStatus(BaseModel):
    """Schema for registration availability status."""

    allowed: bool
    message: Optional[str] = None


class CSRFToken(BaseModel):
    """Schema for CSRF token response."""

    token: str


class UserStatusUpdate(BaseModel):
    """Schema for updating user status (enable/disable)."""

    is_active: bool = Field(..., description="User active status")

    model_config = ConfigDict(json_schema_extra={"example": {"is_active": False}})


class UserDeletionResponse(BaseModel):
    """Schema for user deletion response."""

    success: bool = Field(..., description="Deletion success status")
    message: str = Field(..., description="Deletion result message")
    user_id: int = Field(..., description="ID of deleted user")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "User successfully deleted",
                "user_id": 123,
            }
        }
    )
