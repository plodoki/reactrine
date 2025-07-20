"""Database configuration and connection string management."""

import os
import threading
from typing import Optional
from urllib.parse import quote_plus

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings

from .secrets import get_postgres_password

__all__ = [
    "DatabaseSettings",
    "get_database_settings",
]


class DatabaseSettings(BaseSettings):
    """Database-specific configuration settings."""

    # Database configuration
    POSTGRES_SERVER: str = Field(default="postgres")
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_DB: str = Field(default="app")

    @property
    def POSTGRES_PASSWORD(self) -> str:
        """Get PostgreSQL password from secrets or environment."""
        return get_postgres_password()

    @property
    def DATABASE_URL(self) -> str:
        """
        Assemble the DATABASE_URL from individual Postgres settings and secrets.
        """
        # Check if DATABASE_URL is explicitly set in environment
        env_database_url = os.getenv("DATABASE_URL")
        if env_database_url:
            return env_database_url

        # Build the DSN from components
        try:
            # URL-encode the password to handle special characters
            encoded_password = quote_plus(self.POSTGRES_PASSWORD)
            return str(
                PostgresDsn.build(
                    scheme="postgresql",
                    username=self.POSTGRES_USER,
                    password=encoded_password,
                    host=self.POSTGRES_SERVER,
                    path=self.POSTGRES_DB,
                )
            )
        except ValueError as e:
            raise ValueError(f"Invalid database configuration: {e}") from e
        except Exception as e:
            raise ValueError(f"Error assembling DATABASE_URL: {e}") from e

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """
        Get the AsyncIO compatible database URL (with asyncpg driver).
        Used for main application database connections.
        """
        url = self.DATABASE_URL
        # Guard against unset or non-string DATABASE_URL
        if not url or not isinstance(url, str):
            raise ValueError("DATABASE_URL is not set")
        if url.startswith("postgresql://"):
            # Ensure the proper asyncpg driver is used
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql+psycopg2://"):
            # Replace psycopg2 with asyncpg
            return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        return url  # Already has the right driver or is a non-standard format

    class Config:
        case_sensitive = True


# Global database settings instance
_database_settings: Optional[DatabaseSettings] = None
_database_settings_lock = threading.Lock()


def get_database_settings() -> DatabaseSettings:
    """
    Get the global database settings instance.

    Uses threading lock to ensure thread-safe singleton initialization.

    Returns:
        Database settings instance
    """
    global _database_settings
    if _database_settings is None:
        with _database_settings_lock:
            # Double-checked locking pattern to avoid multiple instances
            if _database_settings is None:
                _database_settings = DatabaseSettings()
    return _database_settings
