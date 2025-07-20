from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .api_key import ApiKey
    from .refresh_token import RefreshToken
    from .role import Role


class User(SQLModel, table=True):
    """User model for authentication and authorization."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field(
        description="Hashed password (empty string for social-only accounts)"
    )
    auth_provider: str = Field(
        default="email", description="Authentication provider (email, google)"
    )
    is_active: bool = Field(
        default=True, description="Whether the user account is active"
    )
    role_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("role.id"), nullable=True, index=True),
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    role: Optional["Role"] = Relationship(back_populates="users")
    refresh_tokens: List["RefreshToken"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    api_keys: List["ApiKey"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
