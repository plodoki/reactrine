# Enhanced Secret Management

The Reactrine includes an enhanced secret management system that provides detailed tracking and auditing capabilities for better debugging and security monitoring.

## Overview

The secret management system reads secrets from multiple sources in order of priority:

1. **Docker Secrets** (`/run/secrets/<secret_name>`) - Production environment
2. **Local Files** (`secrets/<secret_name>.txt`) - Development environment
3. **Environment Variables** (`<SECRET_NAME>`) - Fallback option
4. **Default Values** - Provided as function parameter

## API Reference

### Basic Usage (Backward Compatible)

```python
from app.utils.secrets import read_secret

# Simple secret reading
api_key = read_secret("openai_api_key")
db_password = read_secret("postgres_password", default="development_password")
```

### Enhanced Usage with Detailed Information

```python
from app.utils.secrets import read_secret_detailed, SecretResult

# Get detailed information about secret resolution
result: SecretResult = read_secret_detailed("openai_api_key")

print(f"Value: {result.value}")
print(f"Source: {result.source}")  # "docker_secret", "local_file", "environment", "default", or "none"
print(f"Found: {result.found}")   # True if actual secret found (False for defaults)
print(f"Attempted sources: {result.attempted_sources}")
print(f"Error message: {result.error_message}")  # None if no errors
```

### Security Auditing

```python
from app.utils.secrets import audit_secret_resolution, log_secret_audit

# Audit multiple secrets at once
secrets_to_check = ["postgres_password", "openai_api_key", "secret_key"]
audit_results = audit_secret_resolution(secrets_to_check)

for name, result in audit_results.items():
    status = "✅ Found" if result.found else "❌ Missing"
    print(f"{name}: {status} from {result.source}")

# Detailed logging for debugging (values redacted by default)
log_secret_audit(secrets_to_check, log_values=False)  # Safe for production
log_secret_audit(secrets_to_check, log_values=True)   # Development only - DANGEROUS!
```

## SecretResult Dataclass

The `SecretResult` dataclass provides structured information about secret resolution:

```python
@dataclass
class SecretResult:
    value: Optional[str]           # The actual secret value
    source: str                    # Where the secret was found
    found: bool                    # Whether the secret was found
    secret_name: str              # Original secret name requested
    attempted_sources: list[str]   # List of sources that were tried
    error_message: Optional[str]   # Error message if reading failed
```

### Source Types

- `"docker_secret"` - Secret found in Docker secrets mount (`/run/secrets/`)
- `"local_file"` - Secret found in local development file (`secrets/<name>.txt`)
- `"environment"` - Secret found in environment variable
- `"default"` - Using provided default value (secret not found)
- `"none"` - No secret found and no default provided

## Common Use Cases

### 1. Debugging Secret Resolution Issues

```python
from app.utils.secrets import read_secret_detailed

def debug_database_connection():
    password_result = read_secret_detailed("postgres_password")

    if not password_result.found:
        print(f"❌ Database password not found!")
        print(f"Attempted sources: {password_result.attempted_sources}")
        print(f"Error: {password_result.error_message}")
        return False

    print(f"✅ Database password found in: {password_result.source}")
    return True
```

### 2. Security Audit Script

```python
from app.utils.secrets import audit_secret_resolution

def security_audit():
    critical_secrets = [
        "postgres_password",
        "secret_key",
        "openai_api_key",
        "aws_access_key_id",
        "aws_secret_access_key"
    ]

    audit_results = audit_secret_resolution(critical_secrets)

    # Check for missing secrets
    missing_secrets = [name for name, result in audit_results.items() if not result.found]
    if missing_secrets:
        print(f"⚠️ Missing critical secrets: {missing_secrets}")

    # Check for environment variable secrets (less secure)
    env_secrets = [name for name, result in audit_results.items()
                   if result.source == "environment"]
    if env_secrets:
        print(f"🌍 Secrets from environment (consider moving to files): {env_secrets}")
```

### 3. Development Environment Verification

```python
from app.utils.secrets import log_secret_audit

def verify_dev_environment():
    """Verify that all required secrets are available in development."""
    required_secrets = ["postgres_password", "openai_api_key", "secret_key"]

    print("🔍 Development Environment Secret Audit:")
    log_secret_audit(required_secrets, log_values=False)
```

## Security Considerations

### ✅ Safe Practices

- Use `read_secret_detailed()` for debugging secret resolution
- Use `log_secret_audit()` with `log_values=False` (default)
- Use `audit_secret_resolution()` for security monitoring
- Store secrets in Docker secrets or local files rather than environment variables

### ⚠️ Cautions

- Only use `log_values=True` in development environments
- Be careful when logging `SecretResult` objects as they contain actual values
- Regularly audit secret sources and update as needed

### ❌ Never Do

- Log actual secret values in production
- Store secrets in code or version control
- Use `log_values=True` in production environments
- Print or log `SecretResult.value` in production logs

## Integration with Configuration

The enhanced secret management integrates seamlessly with the existing configuration system:

```python
# In app/core/config.py
@property
def OPENAI_API_KEY(self) -> str | None:
    return read_secret("openai_api_key")

# For debugging configuration issues
from app.utils.secrets import read_secret_detailed

def debug_openai_config():
    result = read_secret_detailed("openai_api_key")
    if not result.found:
        print(f"OpenAI API key not found: {result.error_message}")
    else:
        print(f"OpenAI API key loaded from: {result.source}")
```

## Migration from Legacy Code

The enhanced secret management is fully backward compatible. Existing code using `read_secret()` will continue to work unchanged:

```python
# Old code - still works
password = read_secret("postgres_password", default="dev_password")

# New code - enhanced debugging
result = read_secret_detailed("postgres_password", default="dev_password")
password = result.value  # Same value as above

# Or use the old function for simple cases
password = read_secret("postgres_password", default="dev_password")
```

## Best Practices

1. **Use enhanced functions during development** for better debugging
2. **Regularly audit secrets** using `audit_secret_resolution()`
3. **Prefer file-based secrets** over environment variables for better security
4. **Never log secret values** in production environments
5. **Monitor secret sources** and ensure they're loaded from expected locations
6. **Use default values carefully** - they should only be for non-sensitive development defaults

## Example Output

When using the enhanced secret management, you might see output like:

```
🔍 Secret Resolution Audit:
Secret: postgres_password
  Value: [REDACTED]
  Source: local_file
  Found: True
  Attempted sources: docker_secret, local_file

Secret: openai_api_key
  Value: [REDACTED]
  Source: environment
  Found: True
  Attempted sources: docker_secret, local_file, environment

Secret: missing_secret
  Value: None
  Source: none
  Found: False
  Attempted sources: docker_secret, local_file, environment
  Error: Secret 'missing_secret' not found in any source
```

This enhanced visibility makes it much easier to debug secret resolution issues and maintain security compliance.
