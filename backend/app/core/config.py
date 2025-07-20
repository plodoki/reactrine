"""Core application configuration."""

import os
from typing import List, Optional

from pydantic import EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .database_config import get_database_settings
from .secrets import (
    get_aws_access_key_id,
    get_aws_secret_access_key,
    get_openai_api_key,
    get_openrouter_api_key,
    get_secret_key,
    get_session_secret_key,
)

__all__ = [
    "Settings",
    "get_settings",
]


class Settings(BaseSettings):
    """
    Application settings.

    Reads configuration from environment files and secrets from Docker secrets.
    For non-Docker environments, falls back to environment variables.
    """

    # API configuration
    # Base path for version 1 of the API
    API_V1_STR: str = "/api/v1"
    # Application metadata
    API_TITLE: str = "Reactrine API"
    API_DESCRIPTION: str = "API for the Reactrine"
    API_VERSION: str = "0.1.0"
    # Documentation and OpenAPI endpoints, under the v1 prefix
    DOCS_URL: str = f"{API_V1_STR}/docs"
    REDOC_URL: str = f"{API_V1_STR}/redoc"
    OPENAPI_URL: str = f"{API_V1_STR}/openapi.json"

    # Security - read from secrets with proper validation
    SECRET_KEY: str = Field(default_factory=get_secret_key)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes for security
    JWT_ALGORITHM: str = "HS256"

    # Session secret - separate from JWT secret for security
    SESSION_SECRET_KEY: str = Field(default_factory=get_session_secret_key)

    # Registration settings
    ALLOW_REGISTRATION: bool = Field(
        default=True, description="Allow new user registrations"
    )
    REGISTRATION_DISABLED_MESSAGE: str = Field(
        default="New user registrations are currently disabled. Please contact an administrator.",
        description="Message to show when registration is disabled",
    )

    # Google OAuth settings
    GOOGLE_OAUTH_CLIENT_ID: str = Field(
        default="", description="Google OAuth Client ID"
    )
    GOOGLE_OAUTH_CLIENT_SECRET: str = Field(
        default="", description="Google OAuth Client Secret"
    )

    # CORS configuration
    ALLOWED_ORIGINS_STR: str = "http://localhost:3000"

    # CORS security configuration (not configurable via environment)
    @property
    def CORS_ALLOW_METHODS(self) -> List[str]:
        """Get the list of allowed CORS methods."""
        return ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

    @property
    def CORS_ALLOW_HEADERS(self) -> List[str]:
        """Get the list of allowed CORS headers."""
        return ["Authorization", "Content-Type", "Accept", "X-CSRF-Token"]

    # LLM configuration - secrets read from Docker secrets
    LLM_PROVIDER: str = Field(default="openrouter", description="Default LLM provider")
    DEFAULT_LLM_MODEL: str = Field(
        default="gpt-4o-mini", description="Default LLM model"
    )
    BEDROCK_REGION: str = Field(default="us-east-1", description="AWS Bedrock region")
    BEDROCK_MODEL: str = Field(
        default="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        description="AWS Bedrock model",
    )
    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1", description="OpenRouter API base URL"
    )
    OPENROUTER_MODEL: str = Field(
        default="google/gemini-2.5-flash", description="OpenRouter model"
    )
    LMSTUDIO_BASE_URL: str = Field(
        default="http://192.168.178.191:1234/v1", description="LMStudio base URL"
    )
    LMSTUDIO_MODEL: str = Field(default="local-model", description="LMStudio model")

    # LLM secrets (delegated to secrets module)
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        return get_openai_api_key()

    @property
    def OPENROUTER_API_KEY(self) -> Optional[str]:
        return get_openrouter_api_key()

    @property
    def AWS_ACCESS_KEY_ID(self) -> Optional[str]:
        return get_aws_access_key_id()

    @property
    def AWS_SECRET_ACCESS_KEY(self) -> Optional[str]:
        return get_aws_secret_access_key()

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """
        Get the list of allowed origins for CORS.

        Returns a list of origins split by comma from the ALLOWED_ORIGINS_STR value.
        """
        if not self.ALLOWED_ORIGINS_STR:
            return ["http://localhost:3000"]

        if "," in self.ALLOWED_ORIGINS_STR:
            return [
                origin.strip()
                for origin in self.ALLOWED_ORIGINS_STR.split(",")
                if origin.strip()
            ]

        return [self.ALLOWED_ORIGINS_STR.strip()]

    # Trusted hosts configuration - default to localhost for security
    TRUSTED_HOSTS_STR: str = "localhost,127.0.0.1"

    @property
    def TRUSTED_HOSTS(self) -> List[str]:
        """
        Get the list of allowed hosts for TrustedHost middleware.
        """
        # Allow all hosts in test and development environments for compatibility
        if self.ENVIRONMENT in ["test", "development"]:
            return ["*"]

        if not self.TRUSTED_HOSTS_STR:
            return []
        return [
            host.strip() for host in self.TRUSTED_HOSTS_STR.split(",") if host.strip()
        ]

    # Environment detection for Docker vs local development
    @property
    def IS_DOCKER(self) -> bool:
        """Determine if we're running in a Docker container."""
        # Check environment variable first (most reliable)
        docker_env = os.getenv("DOCKER_CONTAINER")
        if docker_env:
            return docker_env.lower() in ("true", "1", "yes")

        # Fallback to file-based detection
        # Note: These are sync operations but only called during startup/config initialization
        # Common ways to detect Docker:
        # 1. Check for /.dockerenv file
        if os.path.exists("/.dockerenv"):
            return True
        # 2. Check for docker in cgroup
        try:
            with open("/proc/1/cgroup") as f:
                return "docker" in f.read()
        except (OSError, FileNotFoundError, PermissionError):
            pass
        return False

    # Database configuration (delegated to database_config module)
    @property
    def DATABASE_URL(self) -> str:
        """Get the database URL from database settings."""
        return get_database_settings().DATABASE_URL

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Get the async database URL from database settings."""
        return get_database_settings().ASYNC_DATABASE_URL

    # Email configuration
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = ""
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: Optional[EmailStr] = None
    EMAIL_TEST_USER: Optional[EmailStr] = None

    # Environment settings
    ENVIRONMENT: str = "development"

    @field_validator("ENVIRONMENT")
    def environment_must_be_valid(cls, v: str) -> str:
        if v not in ["development", "staging", "production", "test"]:
            raise ValueError(
                "Environment must be one of: development, staging, production, test"
            )
        return v

    @property
    def DEBUG(self) -> bool:
        """
        Debug mode is enabled for non-production environments.
        """
        return self.ENVIRONMENT != "production"

    # Logging configuration
    LOG_LEVEL: str = "INFO"
    # Session configuration
    SESSION_COOKIE_MAX_AGE: int = 60 * 60 * 24 * 7  # 7 days

    # Background Tasks Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="")
    CELERY_RESULT_BACKEND: str = Field(default="")

    @property
    def CELERY_BROKER_URL_COMPUTED(self) -> str:
        """Get the Celery broker URL, defaulting to REDIS_URL if not set."""
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def CELERY_RESULT_BACKEND_COMPUTED(self) -> str:
        """Get the Celery result backend URL, defaulting to REDIS_URL with different DB."""
        if self.CELERY_RESULT_BACKEND:
            return self.CELERY_RESULT_BACKEND
        # Use different Redis DB for results to avoid key conflicts
        if self.REDIS_URL.endswith("/0"):
            return self.REDIS_URL.replace("/0", "/1")
        return (
            f"{self.REDIS_URL}/1"
            if not self.REDIS_URL.endswith("/")
            else f"{self.REDIS_URL}1"
        )

    # RBAC configuration
    INITIAL_ADMIN_EMAIL: Optional[str] = Field(
        default=None, description="Email of user to promote to admin on startup"
    )

    # Base app directory
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Configure to read from environment variables only (no .env file)
    # Environment variables are provided by Docker Compose env_file and environment sections
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")


# Create a global settings object
settings = Settings()


def get_settings() -> Settings:
    """
    Returns the settings object. This function is used for dependency injection in FastAPI.
    """
    return settings
