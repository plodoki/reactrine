"""Secret key management for the application."""

import os
from typing import Optional

from app.utils.secrets import read_secret

__all__ = [
    "get_secret_key",
    "get_session_secret_key",
    "get_openai_api_key",
    "get_openrouter_api_key",
    "get_aws_access_key_id",
    "get_aws_secret_access_key",
    "get_postgres_password",
]


def get_secret_key() -> str:
    """
    Get SECRET_KEY from secrets, raising an error if not found.
    This function is strict and does not allow fallback to runtime-generated keys.
    """
    secret = read_secret("secret_key")
    if secret:
        return secret

    # For test environments, allow a default test key.
    # This prevents tests from failing in CI/CD environments where secrets aren't mounted.
    if os.getenv("ENVIRONMENT") == "test":
        return "test-secret-key-for-automated-tests-only"

    raise ValueError(
        "SECRET_KEY not found. It must be provided via a 'secret_key.txt' file "
        "in the 'secrets/' directory or as an environment variable."
    )


def get_session_secret_key() -> str:
    """
    Get SESSION_SECRET_KEY from secrets, raising an error if not found.
    This function is strict and does not allow fallback to runtime-generated keys.
    """
    secret = read_secret("session_secret_key")
    if secret:
        return secret

    # For test environments, allow a default test key.
    if os.getenv("ENVIRONMENT") == "test":
        return "test-session-secret-key-for-automated-tests-only"

    raise ValueError(
        "SESSION_SECRET_KEY not found. It must be provided via a 'session_secret_key.txt' "
        "file in the 'secrets/' directory or as an environment variable."
    )


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from secrets."""
    return read_secret("openai_api_key")


def get_openrouter_api_key() -> Optional[str]:
    """Get OpenRouter API key from secrets."""
    return read_secret("openrouter_api_key")


def get_aws_access_key_id() -> Optional[str]:
    """Get AWS access key ID from secrets."""
    return read_secret("aws_access_key_id")


def get_aws_secret_access_key() -> Optional[str]:
    """Get AWS secret access key from secrets."""
    return read_secret("aws_secret_access_key")


def get_postgres_password() -> str:
    """
    Get PostgreSQL password from secrets, environment, or fail securely.

    This function follows the environment-aware pattern used by other secret functions:
    1. First attempt reading from secrets (Docker secrets or local file)
    2. Fallback to environment variable POSTGRES_PASSWORD
    3. For test environments only, use a safe test default
    4. Otherwise raise an error for security
    """
    # Try secrets first
    secret = read_secret("postgres_password")
    if secret:
        return secret

    # Fallback to environment variable
    env_password = os.getenv("POSTGRES_PASSWORD")
    if env_password:
        return env_password

    # For test environments, allow a default test password
    if os.getenv("ENVIRONMENT") == "test":
        return "test-postgres-password-for-automated-tests-only"

    raise ValueError(
        "POSTGRES_PASSWORD not found. It must be provided via a 'postgres_password.txt' file "
        "in the 'secrets/' directory or as the POSTGRES_PASSWORD environment variable."
    )
