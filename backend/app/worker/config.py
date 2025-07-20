"""Celery configuration settings."""

from app.core.config import settings

# Celery configuration
broker_url = settings.CELERY_BROKER_URL_COMPUTED
result_backend = settings.CELERY_RESULT_BACKEND_COMPUTED

# Task discovery
include = [
    "app.tasks.example_task",
    # Add new task modules here
]

# Serialization and security
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# Task execution
task_track_started = True
task_time_limit = 30 * 60  # 30 minutes
task_soft_time_limit = 25 * 60  # 25 minutes
worker_prefetch_multiplier = 1
task_acks_late = True
worker_disable_rate_limits = False

# Add test-specific settings
if settings.ENVIRONMENT == "test":
    task_always_eager = True
    task_eager_propagates = True

# Results
result_expires = 3600  # 1 hour
result_persistent = True

# Timezone
timezone = "UTC"
enable_utc = True
