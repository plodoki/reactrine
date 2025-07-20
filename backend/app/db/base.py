"""
Database base configuration for SQLModel.

This module provides the base SQLModel class that all database models should inherit from.
It ensures proper table creation and metadata management for Alembic migrations.
"""

# Import all models here to ensure they are registered with SQLModel.metadata
# This is important for Alembic to detect model changes for migrations
from sqlmodel import SQLModel

from app.models.api_key import ApiKey  # noqa: F401
from app.models.llm_settings import LLMSettings  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.user import User  # noqa: F401

# from app.models.haiku import Haiku  # Uncomment when Haiku model is created

# Re-export SQLModel and models for convenience
__all__ = ["SQLModel", "ApiKey", "LLMSettings", "User", "Role"]
