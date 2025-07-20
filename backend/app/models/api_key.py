import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class ApiKey(SQLModel, table=True):
    """Database model for storing API keys (Personal Access Tokens)."""

    __table_args__ = (
        # Ensure expires_at is after created_at when set
        CheckConstraint(
            "expires_at IS NULL OR expires_at > created_at",
            name="ck_expires_after_created",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to user
    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    # JWT identifier - unique across all API keys (stored as string)
    jti: str = Field(
        sa_column=Column(String(36), nullable=False, unique=True, index=True)
    )

    # SHA256 hash of the full JWT token for constant-time lookup
    token_hash: str = Field(sa_column=Column(String(64), nullable=False, index=True))

    # Optional user-provided label
    label: Optional[str] = Field(
        default=None, sa_column=Column(String(128), nullable=True)
    )

    # Scopes for future use - default to full access (stored as JSON string)
    scopes_json: str = Field(
        default='["*"]', sa_column=Column("scopes", Text, nullable=False)
    )

    @property
    def scopes(self) -> List[str]:
        """Get scopes as a list."""
        result = json.loads(self.scopes_json)
        # Ensure we return a list of strings as expected
        if isinstance(result, list) and all(isinstance(item, str) for item in result):
            return result
        # Fallback to default if data is corrupted
        return ["*"]

    @scopes.setter
    def scopes(self, value: List[str]) -> None:
        """Set scopes from a list."""
        self.scopes_json = json.dumps(value)

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    expires_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    last_used_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    revoked_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Relationships
    user: "User" = Relationship(back_populates="api_keys")

    @property
    def is_revoked(self) -> bool:
        """Check if the API key has been revoked."""
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False  # No expiry means never expires
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if the API key is active (not revoked and not expired)."""
        return not self.is_revoked and not self.is_expired
