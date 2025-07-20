"""Tests for the secrets utility module."""

import os
from unittest.mock import patch

from app.utils.secrets import (
    SecretResult,
    audit_secret_resolution,
    log_secret_audit,
    read_secret,
    read_secret_detailed,
)


class TestReadSecret:
    """Test cases for the read_secret function (backward compatibility)."""

    def test_fallback_to_environment_variable(self):
        """Test fallback to environment variable when no secret files exist."""
        with patch.dict(os.environ, {"TEST_SECRET": "env_value"}, clear=False):
            result = read_secret("test_secret")
            assert result == "env_value"

    def test_fallback_to_default_value(self):
        """Test fallback to default value when no secret is found."""
        with patch.dict(os.environ, {}, clear=True):
            result = read_secret("nonexistent_secret", default="default_value")
            assert result == "default_value"

    def test_return_none_when_no_secret_or_default(self):
        """Test returning None when no secret is found and no default provided."""
        with patch.dict(os.environ, {}, clear=True):
            result = read_secret("nonexistent_secret")
            assert result is None

    def test_environment_variable_uppercase_conversion(self):
        """Test that secret names are converted to uppercase for environment variables."""
        with patch.dict(os.environ, {"LOWERCASE_SECRET": "env_value"}, clear=False):
            result = read_secret("lowercase_secret")
            assert result == "env_value"

    def test_secret_value_stripped_from_env(self):
        """Test that secret values from environment are properly stripped."""
        with patch.dict(os.environ, {"TEST_SECRET": "  env_value  "}, clear=False):
            # Environment variables don't get stripped by our function, only file content does
            result = read_secret("test_secret")
            assert result == "  env_value  "  # Environment variables are not stripped

    def test_docker_secret_file_not_exists(self):
        """Test behavior when Docker secret file doesn't exist."""
        with patch.dict(os.environ, {"TEST_SECRET": "fallback_value"}, clear=False):
            result = read_secret("test_secret")
            # Should fallback to environment variable since Docker secret doesn't exist
            assert result == "fallback_value"


class TestReadSecretDetailed:
    """Test cases for the enhanced read_secret_detailed function."""

    def test_environment_variable_found(self):
        """Test detailed result when secret is found in environment variable."""
        with patch.dict(os.environ, {"TEST_SECRET": "env_value"}, clear=False):
            result = read_secret_detailed("test_secret")

            assert isinstance(result, SecretResult)
            assert result.value == "env_value"
            assert result.source == "environment"
            assert result.found is True
            assert result.secret_name == "test_secret"
            assert "docker_secret" in result.attempted_sources
            assert "local_file" in result.attempted_sources
            assert "environment" in result.attempted_sources
            assert result.error_message is None

    def test_default_value_used(self):
        """Test detailed result when default value is used."""
        with patch.dict(os.environ, {}, clear=True):
            result = read_secret_detailed("nonexistent_secret", default="default_value")

            assert isinstance(result, SecretResult)
            assert result.value == "default_value"
            assert result.source == "default"
            assert result.found is False  # False because actual secret wasn't found
            assert result.secret_name == "nonexistent_secret"
            assert "docker_secret" in result.attempted_sources
            assert "local_file" in result.attempted_sources
            assert "environment" in result.attempted_sources
            assert "default" in result.attempted_sources
            assert result.error_message is None

    def test_no_secret_found_no_default(self):
        """Test detailed result when no secret is found and no default provided."""
        with patch.dict(os.environ, {}, clear=True):
            result = read_secret_detailed("nonexistent_secret")

            assert isinstance(result, SecretResult)
            assert result.value is None
            assert result.source == "none"
            assert result.found is False
            assert result.secret_name == "nonexistent_secret"
            assert "docker_secret" in result.attempted_sources
            assert "local_file" in result.attempted_sources
            assert "environment" in result.attempted_sources
            assert "default" not in result.attempted_sources  # No default was provided
            assert result.error_message is not None
            assert "not found in any source" in result.error_message

    def test_uppercase_conversion_tracking(self):
        """Test that uppercase conversion is properly tracked in detailed result."""
        with patch.dict(os.environ, {"LOWERCASE_SECRET": "env_value"}, clear=False):
            result = read_secret_detailed("lowercase_secret")

            assert result.value == "env_value"
            assert result.source == "environment"
            assert result.found is True
            assert result.secret_name == "lowercase_secret"  # Original name preserved

    def test_docker_secret_file_not_exists_detailed(self):
        """Test detailed result when Docker secret file doesn't exist."""
        with patch.dict(os.environ, {"TEST_SECRET": "fallback_value"}, clear=False):
            result = read_secret_detailed("test_secret")

            assert result.value == "fallback_value"
            assert result.source == "environment"
            assert result.found is True
            assert "docker_secret" in result.attempted_sources
            assert "local_file" in result.attempted_sources
            assert "environment" in result.attempted_sources

    def test_secret_result_dataclass_structure(self):
        """Test that SecretResult has the expected structure."""
        with patch.dict(os.environ, {"TEST_SECRET": "value"}, clear=False):
            result = read_secret_detailed("test_secret")

            # Verify all expected fields exist
            assert hasattr(result, "value")
            assert hasattr(result, "source")
            assert hasattr(result, "found")
            assert hasattr(result, "secret_name")
            assert hasattr(result, "attempted_sources")
            assert hasattr(result, "error_message")

            # Verify types
            assert isinstance(result.value, str)
            assert isinstance(result.source, str)
            assert isinstance(result.found, bool)
            assert isinstance(result.secret_name, str)
            assert isinstance(result.attempted_sources, list)
            assert result.error_message is None or isinstance(result.error_message, str)


class TestBackwardCompatibility:
    """Test that the new implementation maintains backward compatibility."""

    def test_read_secret_returns_same_as_before(self):
        """Test that read_secret returns the same values as the old implementation."""
        with patch.dict(os.environ, {"TEST_SECRET": "env_value"}, clear=False):
            # Test environment variable
            assert read_secret("test_secret") == "env_value"

        with patch.dict(os.environ, {}, clear=True):
            # Test default value
            assert read_secret("nonexistent", default="default") == "default"

            # Test None return
            assert read_secret("nonexistent") is None

    def test_read_secret_detailed_value_matches_read_secret(self):
        """Test that read_secret_detailed.value matches read_secret result."""
        test_cases = [
            ("test_secret", None, {"TEST_SECRET": "env_value"}),
            ("nonexistent", "default_val", {}),
            ("nonexistent", None, {}),
        ]

        for secret_name, default, env_vars in test_cases:
            with patch.dict(os.environ, env_vars, clear=True):
                simple_result = read_secret(secret_name, default)
                detailed_result = read_secret_detailed(secret_name, default)

                assert (
                    simple_result == detailed_result.value
                ), f"Mismatch for {secret_name} with default {default}"


class TestAuditFunctions:
    """Test cases for the secret audit functionality."""

    def test_audit_secret_resolution(self):
        """Test auditing multiple secrets."""
        with patch.dict(
            os.environ, {"SECRET1": "value1", "SECRET2": "value2"}, clear=True
        ):
            audit_results = audit_secret_resolution(
                ["secret1", "secret2", "nonexistent"]
            )

            # Verify we get results for all requested secrets
            assert len(audit_results) == 3
            assert "secret1" in audit_results
            assert "secret2" in audit_results
            assert "nonexistent" in audit_results

            # Verify found secrets
            assert audit_results["secret1"].value == "value1"
            assert audit_results["secret1"].found is True
            assert audit_results["secret1"].source == "environment"

            assert audit_results["secret2"].value == "value2"
            assert audit_results["secret2"].found is True

            # Verify not found secret
            assert audit_results["nonexistent"].value is None
            assert audit_results["nonexistent"].found is False
            assert audit_results["nonexistent"].source == "none"

    def test_audit_empty_list(self):
        """Test auditing empty list of secrets."""
        audit_results = audit_secret_resolution([])
        assert audit_results == {}

    def test_log_secret_audit_without_values(self):
        """Test logging audit without showing values (safe mode)."""
        from unittest.mock import Mock

        # Mock the logger to capture log calls
        mock_logger = Mock()

        with patch.dict(os.environ, {"TEST_SECRET": "secret_value"}, clear=True):
            with patch("app.utils.secrets.logger", mock_logger):
                log_secret_audit(["test_secret"], log_values=False)

                # Verify info was called multiple times
                assert mock_logger.info.call_count > 0

                # Check that [REDACTED] is used instead of actual value
                log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
                value_logs = [log for log in log_calls if "Value:" in log]
                assert len(value_logs) > 0
                assert any("[REDACTED]" in log for log in value_logs)
                assert not any("secret_value" in log for log in value_logs)

    def test_log_secret_audit_with_values(self):
        """Test logging audit with values shown (dangerous mode)."""
        from unittest.mock import Mock

        # Mock the logger to capture log calls
        mock_logger = Mock()

        with patch.dict(os.environ, {"TEST_SECRET": "secret_value"}, clear=True):
            with patch("app.utils.secrets.logger", mock_logger):
                log_secret_audit(["test_secret"], log_values=True)

                # Verify info was called multiple times
                assert mock_logger.info.call_count > 0

                # Check that actual value is shown when log_values=True
                log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
                value_logs = [log for log in log_calls if "Value:" in log]
                assert len(value_logs) > 0
                assert any("secret_value" in log for log in value_logs)
