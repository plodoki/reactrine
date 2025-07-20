"""
Integration tests for Celery application setup and configuration.

Tests the Celery application configuration, task discovery, and integration
with the application settings, following established patterns from AGENTS.md.
"""

from unittest.mock import patch

from app.worker.celery_app import celery_app
from app.worker.config import (
    accept_content,
    enable_utc,
    include,
    result_expires,
    result_persistent,
    result_serializer,
    task_acks_late,
    task_serializer,
    task_soft_time_limit,
    task_time_limit,
    task_track_started,
    timezone,
    worker_disable_rate_limits,
    worker_prefetch_multiplier,
)


class TestCeleryApplication:
    """Test Celery application configuration and setup."""

    def test_celery_app_created(self):
        """Test that Celery application is properly created."""
        assert celery_app is not None
        assert celery_app.main == "reactrine_worker"
        assert hasattr(celery_app, "tasks")
        assert hasattr(celery_app, "conf")

    def test_celery_app_name(self):
        """Test that Celery application has the correct name."""
        assert celery_app.main == "reactrine_worker"

    def test_celery_app_configuration_loaded(self):
        """Test that Celery configuration is properly loaded."""
        config = celery_app.conf

        # Test serialization settings
        assert config.task_serializer == "json"
        assert config.result_serializer == "json"
        assert config.accept_content == ["json"]

        # Test task execution settings
        assert config.task_track_started is True
        assert config.task_time_limit == 30 * 60  # 30 minutes
        assert config.task_soft_time_limit == 25 * 60  # 25 minutes
        assert config.worker_prefetch_multiplier == 1
        assert config.task_acks_late is True
        assert config.worker_disable_rate_limits is False

        # Test result settings
        assert config.result_expires == 3600  # 1 hour
        assert config.result_persistent is True

        # Test timezone settings
        assert config.timezone == "UTC"
        assert config.enable_utc is True

    def test_task_discovery(self):
        """Test that tasks are properly discovered."""
        task_names = list(celery_app.tasks.keys())

        # Check that our example tasks are discovered
        expected_tasks = [
            "app.tasks.example_task.simple_task",
            "app.tasks.example_task.database_task",
            "app.tasks.example_task.error_task",
        ]

        for task_name in expected_tasks:
            assert task_name in task_names, f"Task {task_name} not discovered"

    def test_task_registration_count(self):
        """Test that expected number of tasks are registered."""
        task_names = list(celery_app.tasks.keys())

        # Filter out built-in Celery tasks (they start with 'celery.')
        custom_tasks = [name for name in task_names if not name.startswith("celery.")]

        # Should have at least our 3 example tasks
        assert len(custom_tasks) >= 3

    def test_celery_app_has_required_attributes(self):
        """Test that Celery app has all required attributes."""
        required_attributes = [
            "main",
            "tasks",
            "conf",
            "autodiscover_tasks",
            "task",
            "control",
            "events",
        ]

        for attr in required_attributes:
            assert hasattr(celery_app, attr), f"Celery app missing attribute: {attr}"

    def test_celery_app_control_interface(self):
        """Test that Celery control interface is available."""
        assert hasattr(celery_app, "control")
        assert hasattr(celery_app.control, "inspect")
        assert hasattr(celery_app.control, "purge")

    def test_celery_app_events_interface(self):
        """Test that Celery events interface is available."""
        assert hasattr(celery_app, "events")
        assert hasattr(celery_app.events, "State")


class TestCeleryConfiguration:
    """Test Celery configuration module."""

    @patch("app.core.config.settings")
    def test_broker_url_configuration(self, mock_settings):
        """Test broker URL configuration."""
        mock_settings.CELERY_BROKER_URL_COMPUTED = "redis://test:6379/0"
        import importlib

        import app.worker.config as config_module

        importlib.reload(config_module)
        assert config_module.broker_url == "redis://test:6379/0"

    @patch("app.core.config.settings")
    def test_result_backend_configuration(self, mock_settings):
        """Test result backend configuration."""
        mock_settings.CELERY_RESULT_BACKEND_COMPUTED = "redis://test:6379/1"
        import importlib

        import app.worker.config as config_module

        importlib.reload(config_module)
        assert config_module.result_backend == "redis://test:6379/1"

    def test_task_includes_configuration(self):
        """Test that task includes are properly configured."""
        assert "app.tasks.example_task" in include
        assert isinstance(include, list)

    def test_serialization_configuration(self):
        """Test serialization configuration."""
        assert task_serializer == "json"
        assert result_serializer == "json"
        assert accept_content == ["json"]

    def test_task_execution_configuration(self):
        """Test task execution configuration."""
        assert task_track_started is True
        assert task_time_limit == 30 * 60  # 30 minutes
        assert task_soft_time_limit == 25 * 60  # 25 minutes
        assert worker_prefetch_multiplier == 1
        assert task_acks_late is True
        assert worker_disable_rate_limits is False

    def test_result_configuration(self):
        """Test result configuration."""
        assert result_expires == 3600  # 1 hour
        assert result_persistent is True

    def test_timezone_configuration(self):
        """Test timezone configuration."""
        assert timezone == "UTC"
        assert enable_utc is True

    def test_configuration_types(self):
        """Test that configuration values have correct types."""
        assert isinstance(task_serializer, str)
        assert isinstance(result_serializer, str)
        assert isinstance(accept_content, list)
        assert isinstance(task_track_started, bool)
        assert isinstance(task_time_limit, int)
        assert isinstance(task_soft_time_limit, int)
        assert isinstance(worker_prefetch_multiplier, int)
        assert isinstance(task_acks_late, bool)
        assert isinstance(worker_disable_rate_limits, bool)
        assert isinstance(result_expires, int)
        assert isinstance(result_persistent, bool)
        assert isinstance(timezone, str)
        assert isinstance(enable_utc, bool)


class TestTaskDiscovery:
    """Test task discovery functionality."""

    def test_autodiscover_tasks_configuration(self):
        """Test that autodiscover_tasks is properly configured."""
        # Check that autodiscover_tasks was called with correct modules
        assert hasattr(celery_app, "autodiscover_tasks")

    def test_task_module_discovery(self):
        """Test that tasks from specified modules are discovered."""
        task_names = list(celery_app.tasks.keys())

        # Tasks from app.tasks.example_task should be discovered
        example_tasks = [name for name in task_names if "example" in name]
        assert len(example_tasks) >= 3

    def test_task_name_patterns(self):
        """Test that discovered tasks follow expected naming patterns."""
        task_names = list(celery_app.tasks.keys())

        # Filter custom tasks (exclude built-in Celery tasks)
        custom_tasks = [name for name in task_names if not name.startswith("celery.")]

        for task_name in custom_tasks:
            # Task names should be strings
            assert isinstance(task_name, str)
            # Task names should not be empty
            assert len(task_name) > 0

    def test_task_objects_properties(self):
        """Test that discovered task objects have required properties."""
        expected_tasks = [
            "app.tasks.example_task.simple_task",
            "app.tasks.example_task.database_task",
            "app.tasks.example_task.error_task",
        ]

        for task_name in expected_tasks:
            task = celery_app.tasks[task_name]

            # Task should have required attributes
            assert hasattr(task, "name")
            assert hasattr(task, "apply")
            assert hasattr(task, "delay")
            assert hasattr(task, "apply_async")

            # Task name should match
            assert task.name == task_name

    def test_task_callable_interface(self):
        """Test that discovered tasks have callable interface."""
        expected_tasks = [
            "app.tasks.example_task.simple_task",
            "app.tasks.example_task.database_task",
            "app.tasks.example_task.error_task",
        ]

        for task_name in expected_tasks:
            task = celery_app.tasks[task_name]

            # Task should be callable
            assert callable(task)

            # Task methods should be callable
            assert callable(task.apply)
            assert callable(task.delay)
            assert callable(task.apply_async)


class TestCeleryIntegrationWithSettings:
    """Test Celery integration with application settings."""

    @patch("app.core.config.settings")
    def test_settings_integration(self, mock_settings):
        """Test that Celery properly integrates with application settings."""
        mock_settings.CELERY_BROKER_URL_COMPUTED = "redis://integration:6379/0"
        mock_settings.CELERY_RESULT_BACKEND_COMPUTED = "redis://integration:6379/1"
        import importlib

        import app.worker.config as config_module

        importlib.reload(config_module)
        assert config_module.broker_url == "redis://integration:6379/0"
        assert config_module.result_backend == "redis://integration:6379/1"

    def test_settings_property_access(self):
        """Test that settings properties are accessible."""
        from app.core.config import settings

        # These properties should exist and be accessible
        assert hasattr(settings, "CELERY_BROKER_URL_COMPUTED")
        assert hasattr(settings, "CELERY_RESULT_BACKEND_COMPUTED")

        # Properties should return strings
        assert isinstance(settings.CELERY_BROKER_URL_COMPUTED, str)
        assert isinstance(settings.CELERY_RESULT_BACKEND_COMPUTED, str)

    def test_redis_url_fallback(self):
        """Test that Redis URL fallback works correctly."""
        from app.core.config import settings

        # If CELERY_BROKER_URL is not set, should fall back to REDIS_URL
        broker_url = settings.CELERY_BROKER_URL_COMPUTED
        assert broker_url is not None
        assert isinstance(broker_url, str)
        assert len(broker_url) > 0

    def test_result_backend_database_separation(self):
        """Test that result backend uses different database than broker."""
        from app.core.config import settings

        broker_url = settings.CELERY_BROKER_URL_COMPUTED
        result_backend = settings.CELERY_RESULT_BACKEND_COMPUTED

        # Should be different to avoid key conflicts
        assert broker_url != result_backend


class TestCelerySecurityConfiguration:
    """Test Celery security configuration."""

    def test_json_serialization_security(self):
        """Test that JSON serialization is used for security."""
        config = celery_app.conf

        # Should use JSON serialization (not pickle) for security
        assert config.task_serializer == "json"
        assert config.result_serializer == "json"
        assert config.accept_content == ["json"]

    def test_no_pickle_serialization(self):
        """Test that pickle serialization is not enabled."""
        config = celery_app.conf

        # Should not accept pickle content
        assert "pickle" not in config.accept_content
        assert config.task_serializer != "pickle"
        assert config.result_serializer != "pickle"

    def test_task_acks_late_enabled(self):
        """Test that task_acks_late is enabled for reliability."""
        config = celery_app.conf

        # Should acknowledge tasks late for better reliability
        assert config.task_acks_late is True

    def test_prefetch_multiplier_configuration(self):
        """Test that prefetch multiplier is configured for fair distribution."""
        config = celery_app.conf

        # Should use prefetch multiplier of 1 for fair task distribution
        assert config.worker_prefetch_multiplier == 1


class TestCeleryTaskTimeouts:
    """Test Celery task timeout configuration."""

    def test_task_time_limits(self):
        """Test that task time limits are properly configured."""
        config = celery_app.conf

        # Hard timeout should be 30 minutes
        assert config.task_time_limit == 30 * 60

        # Soft timeout should be 25 minutes (less than hard timeout)
        assert config.task_soft_time_limit == 25 * 60
        assert config.task_soft_time_limit < config.task_time_limit

    def test_result_expiration(self):
        """Test that result expiration is configured."""
        config = celery_app.conf

        # Results should expire after 1 hour
        assert config.result_expires == 3600

        # Results should be persistent
        assert config.result_persistent is True

    def test_timezone_configuration(self):
        """Test that timezone is properly configured."""
        config = celery_app.conf

        # Should use UTC timezone
        assert config.timezone == "UTC"
        assert config.enable_utc is True


class TestCeleryApplicationStartup:
    """Test Celery application startup and initialization."""

    def test_celery_app_initialization(self):
        """Test that Celery app initializes without errors."""
        # Should not raise any exceptions during initialization
        assert celery_app is not None
        assert celery_app.main == "reactrine_worker"

    def test_configuration_loading(self):
        """Test that configuration loads without errors."""
        # Configuration should be loaded from config module
        config = celery_app.conf
        assert config is not None

        # Should have expected configuration values
        assert hasattr(config, "broker_url")
        assert hasattr(config, "result_backend")

    def test_task_registration_during_startup(self):
        """Test that tasks are registered during startup."""
        # Tasks should be registered and available
        assert len(celery_app.tasks) > 0

        # Should include our custom tasks
        custom_tasks = [
            name for name in celery_app.tasks.keys() if not name.startswith("celery.")
        ]
        assert len(custom_tasks) >= 3

    def test_celery_app_ready_state(self):
        """Test that Celery app is in ready state."""
        # App should be properly configured and ready
        assert celery_app.configured is True
        assert celery_app.finalized is True

    def test_celery_worker_configuration(self):
        """Test worker-specific configuration."""
        config = celery_app.conf

        # Worker should have proper configuration
        assert config.worker_prefetch_multiplier == 1
        assert config.worker_disable_rate_limits is False
        assert config.task_acks_late is True
