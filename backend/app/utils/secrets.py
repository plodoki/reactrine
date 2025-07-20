"""
Utilities for reading secrets from various sources.

This module provides a centralized way to read secrets from:
1. Docker secrets mount point (/run/secrets/)
2. Local secrets directory (for development)
3. Environment variables (fallback)
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

__all__ = [
    "SecretResult",
    "read_secret",
    "read_secret_detailed",
    "audit_secret_resolution",
    "log_secret_audit",
]


@dataclass
class SecretResult:
    """Result of secret lookup with source tracking and debugging information.

    This dataclass provides detailed information about how and where a secret
    was resolved, enabling better debugging and security auditing.
    """

    value: Optional[str]  # The actual secret value
    source: str  # Source where secret was found: "docker_secret", "local_file", "environment", "default"
    found: bool  # Whether the secret was found in any source
    secret_name: str  # Original secret name requested
    attempted_sources: list[str]  # List of sources that were attempted
    error_message: Optional[str] = None  # Error message if reading failed


def read_secret_detailed(
    secret_name: str, default: Optional[str] = None
) -> SecretResult:
    """
    Read a secret with detailed source tracking and debugging information.

    Docker secrets are mounted at /run/secrets/<secret_name>
    Local development secrets are in ../../secrets/<secret_name>.txt (relative to app directory)
    Falls back to environment variable if secret files don't exist.

    Args:
        secret_name: Name of the secret to read
        default: Default value to return if secret is not found

    Returns:
        SecretResult with detailed information about the secret lookup
    """
    attempted_sources = []
    error_message = None

    # Check Docker secrets mount point first
    secret_file = Path(f"/run/secrets/{secret_name}")
    attempted_sources.append("docker_secret")

    if secret_file.exists():
        try:
            value = secret_file.read_text().strip()
            logger.debug(f"Secret '{secret_name}' found in Docker secrets mount")
            return SecretResult(
                value=value,
                source="docker_secret",
                found=True,
                secret_name=secret_name,
                attempted_sources=attempted_sources.copy(),
            )
        except (PermissionError, OSError) as e:
            error_msg = (
                f"Failed to read Docker secret {secret_name}: {type(e).__name__}"
            )
            logger.warning(error_msg)
            error_message = error_msg
        except Exception as e:
            error_msg = f"Unexpected error reading Docker secret {secret_name}: {type(e).__name__}"
            logger.error(error_msg)
            error_message = error_msg

    # Check local secrets directory (for development outside Docker)
    # Navigate up from app/utils to project root, then to secrets
    local_secret_file = (
        Path(__file__).parent.parent.parent.parent / "secrets" / f"{secret_name}.txt"
    )
    attempted_sources.append("local_file")

    if local_secret_file.exists():
        try:
            value = local_secret_file.read_text().strip()
            logger.debug(f"Secret '{secret_name}' found in local secrets file")
            return SecretResult(
                value=value,
                source="local_file",
                found=True,
                secret_name=secret_name,
                attempted_sources=attempted_sources.copy(),
            )
        except (PermissionError, OSError) as e:
            error_msg = f"Failed to read local secret {secret_name}: {type(e).__name__}"
            logger.warning(error_msg)
            if error_message is None:
                error_message = error_msg
        except Exception as e:
            error_msg = f"Unexpected error reading local secret {secret_name}: {type(e).__name__}"
            logger.error(error_msg)
            if error_message is None:
                error_message = error_msg

    # Fallback to environment variable
    env_var = secret_name.upper()
    attempted_sources.append("environment")
    env_value = os.getenv(env_var)

    if env_value is not None:
        logger.debug(
            f"Secret '{secret_name}' found in environment variable '{env_var}'"
        )
        return SecretResult(
            value=env_value,
            source="environment",
            found=True,
            secret_name=secret_name,
            attempted_sources=attempted_sources.copy(),
        )

    # Use default value if provided
    if default is not None:
        attempted_sources.append("default")
        logger.debug(f"Secret '{secret_name}' not found, using provided default value")
        return SecretResult(
            value=default,
            source="default",
            found=False,  # False because the actual secret wasn't found
            secret_name=secret_name,
            attempted_sources=attempted_sources.copy(),
        )

    # No secret found and no default provided
    logger.warning(
        f"Secret '{secret_name}' not found in any source and no default provided"
    )
    return SecretResult(
        value=None,
        source="none",
        found=False,
        secret_name=secret_name,
        attempted_sources=attempted_sources,
        error_message=error_message
        or f"Secret '{secret_name}' not found in any source",
    )


def read_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Read a secret from Docker secrets mount point, local secrets directory, or environment variable.

    This is the backward-compatible version that maintains the original API.
    For detailed information about secret resolution, use read_secret_detailed().

    Docker secrets are mounted at /run/secrets/<secret_name>
    Local development secrets are in ../../secrets/<secret_name>.txt (relative to app directory)
    Falls back to environment variable if secret files don't exist.

    Args:
        secret_name: Name of the secret to read
        default: Default value to return if secret is not found

    Returns:
        The secret value if found, otherwise the default value
    """
    result = read_secret_detailed(secret_name, default)
    return result.value


def audit_secret_resolution(secret_names: list[str]) -> dict[str, SecretResult]:
    """
    Audit how multiple secrets are resolved for debugging and security analysis.

    This function is useful for:
    - Debugging secret resolution issues
    - Security auditing to understand secret sources
    - Development environment verification

    Args:
        secret_names: List of secret names to audit

    Returns:
        Dictionary mapping secret names to their SecretResult

    Example:
        >>> audit = audit_secret_resolution(['postgres_password', 'openai_api_key'])
        >>> for name, result in audit.items():
        ...     print(f"{name}: {result.source} ({'found' if result.found else 'not found'})")
    """
    return {name: read_secret_detailed(name) for name in secret_names}


def log_secret_audit(secret_names: list[str], log_values: bool = False) -> None:
    """
    Log detailed information about secret resolution for debugging.

    Args:
        secret_names: List of secret names to audit
        log_values: Whether to log actual secret values (DANGEROUS - use only in development)

    Warning:
        Setting log_values=True will log actual secret values, which is a security risk.
        Only use this in development environments for debugging.
    """
    audit_results = audit_secret_resolution(secret_names)

    logger.info("=== Secret Resolution Audit ===")
    for name, result in audit_results.items():
        value_info = (
            result.value if log_values else "[REDACTED]" if result.value else "None"
        )
        logger.info(f"Secret: {name}")
        logger.info(f"  Value: {value_info}")
        logger.info(f"  Source: {result.source}")
        logger.info(f"  Found: {result.found}")
        logger.info(f"  Attempted sources: {', '.join(result.attempted_sources)}")
        if result.error_message:
            logger.warning(f"  Error: {result.error_message}")
        logger.info("")  # Empty line for readability
