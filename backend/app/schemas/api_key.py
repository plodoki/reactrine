"""
Pydantic schemas for Personal API Key management.

These schemas define the request and response models for API key operations.
"""

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiKeyBase(BaseModel):
    """Base schema for API key fields."""

    label: Optional[str] = Field(
        None,
        min_length=1,
        max_length=128,
        description="Optional user-provided label for the API key (1-128 characters, alphanumeric, spaces, hyphens, underscores)",
    )

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: Optional[str]) -> Optional[str]:
        """Validate label format and content."""
        if v is not None:
            # Remove leading/trailing whitespace
            v = v.strip()

            # Check if empty after stripping
            if not v:
                raise ValueError("Label cannot be empty or whitespace only")

            # Check pattern - allow alphanumeric, spaces, hyphens, underscores
            if not re.match(r"^[a-zA-Z0-9\s\-_]+$", v):
                raise ValueError(
                    "Label can only contain letters, numbers, spaces, hyphens, and underscores"
                )

            # Check for consecutive spaces
            if "  " in v:
                raise ValueError("Label cannot contain consecutive spaces")

        return v


class ApiKeyCreate(ApiKeyBase):
    """Schema for creating a new API key."""

    expires_in_days: Optional[int] = Field(
        30,
        ge=1,
        le=365,
        description="Days until expiration (1-365, default 30, None for no expiry)",
    )

    @field_validator("expires_in_days")
    @classmethod
    def validate_expires_in_days(cls, v: Optional[int]) -> Optional[int]:
        """Validate expiration days."""
        if v is not None:
            if v < 1:
                raise ValueError("expires_in_days must be at least 1")
            if v > 365:
                raise ValueError("expires_in_days cannot exceed 365 days")
        return v


class ApiKeyCreated(BaseModel):
    """Schema for API key creation response (includes the actual token)."""

    api_key: "ApiKeyInfo"
    token: str = Field(description="The JWT token - only shown once during creation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "api_key": {
                    "id": 1,
                    "label": "My Development Key",
                    "created_at": "2024-01-01T00:00:00Z",
                    "expires_at": "2024-01-31T00:00:00Z",
                    "last_used_at": None,
                    "is_active": True,
                },
                "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }
    )


class ApiKeyInfo(BaseModel):
    """Schema for API key information (without the actual token)."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="API key ID")
    label: Optional[str] = Field(description="User-provided label")
    created_at: datetime = Field(description="When the key was created")
    expires_at: Optional[datetime] = Field(
        description="When the key expires (None for no expiry)"
    )
    last_used_at: Optional[datetime] = Field(description="When the key was last used")
    is_active: bool = Field(
        description="Whether the key is active (not revoked and not expired)"
    )

    # Note: We never expose the actual token, jti, or token_hash for security


class ApiKeyList(BaseModel):
    """Schema for listing API keys."""

    keys: List[ApiKeyInfo] = Field(description="List of API keys")
    total: int = Field(description="Total number of keys")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "keys": [
                    {
                        "id": 1,
                        "label": "Development Key",
                        "created_at": "2024-01-01T00:00:00Z",
                        "expires_at": "2024-01-31T00:00:00Z",
                        "last_used_at": "2024-01-15T10:30:00Z",
                        "is_active": True,
                    },
                    {
                        "id": 2,
                        "label": "Production Key",
                        "created_at": "2024-01-10T00:00:00Z",
                        "expires_at": None,
                        "last_used_at": None,
                        "is_active": True,
                    },
                ],
                "total": 2,
            }
        }
    )


class ApiKeyRevoked(BaseModel):
    """Schema for API key revocation response."""

    success: bool = Field(description="Whether the revocation was successful")
    message: str = Field(description="Human-readable message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"success": True, "message": "API key revoked successfully"}
        }
    )


class ApiKeyError(BaseModel):
    """Schema for API key error responses."""

    error: str = Field(description="Error message")
    detail: Optional[str] = Field(description="Additional error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "API key not found",
                "detail": "The specified API key does not exist or you don't have permission to access it",
            }
        }
    )
