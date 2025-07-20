"""
Celery application instance.

Provides the main Celery application configured for the FastStack environment.
"""

from celery import Celery

from app.worker import config

# Create Celery application
celery_app = Celery("reactrine_worker")

# Load configuration from config module
celery_app.config_from_object(config)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])

if __name__ == "__main__":
    celery_app.start()
