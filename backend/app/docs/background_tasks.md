# Background Tasks Development Guide

This guide covers developing and deploying background tasks using Celery and Redis in the Reactrine.

## Overview

Background tasks enable asynchronous processing of time-consuming operations without blocking API responses. Common use cases include:

- **Email sending** - Welcome emails, notifications, newsletters
- **File processing** - Image resizing, document conversion, data imports
- **Data synchronization** - Third-party API calls, database migrations
- **Report generation** - PDF creation, analytics processing
- **Cleanup operations** - Log rotation, cache clearing, data archiving

## Architecture

The background task system consists of:

- **Redis**: Message broker and result backend
- **Celery Worker**: Background task processor
- **FastAPI Integration**: API endpoints for task management
- **Database Integration**: Async database operations within tasks

## Creating Tasks

### Simple Tasks

For tasks that don't require database access:

```python
from app.worker.celery_app import celery_app
# Note: send_email is a placeholder function - implement your email service
from app.services.email import send_email  # Example import

@celery_app.task(name="send_welcome_email")
def send_welcome_email(user_email: str, user_name: str) -> dict:
    """Send welcome email to new user."""
    # Email sending logic here
    send_email(
        to=user_email,
        subject="Welcome to Reactrine!",
        template="welcome",
        context={"name": user_name}
    )

    return {
        "status": "sent",
        "recipient": user_email,
        "sent_at": datetime.utcnow().isoformat()
    }
```

### Database Tasks

For tasks that need database access, use the `@task_with_db` decorator:

```python
from app.worker.base_task import task_with_db
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

@task_with_db(name="update_user_stats")
async def update_user_stats(db: AsyncSession, user_id: int) -> dict:
    """Update user statistics in database."""
    user = await db.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Update user statistics
    user.last_activity = datetime.utcnow()
    user.login_count += 1

    await db.commit()

    return {
        "user_id": user_id,
        "updated_at": datetime.utcnow().isoformat(),
        "login_count": user.login_count
    }
```

### Error Handling and Retries

Configure automatic retries for transient failures:

```python
@celery_app.task(
    name="process_payment",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True
)
def process_payment(self, payment_id: str, amount: float) -> dict:
    """Process payment with automatic retries."""
    try:
        # Payment processing logic
        result = payment_gateway.charge(payment_id, amount)
        return {"status": "success", "transaction_id": result.id}
    except PaymentError as e:
        # Log error and re-raise for retry
        logger.error(f"Payment failed: {e}")
        raise
```

### Long-Running Tasks

For tasks that may take a long time, update progress:

```python
@celery_app.task(name="process_large_file", bind=True)
def process_large_file(self, file_path: str) -> dict:
    """Process large file with progress updates."""
    total_lines = count_lines(file_path)
    processed = 0

    with open(file_path, 'r') as f:
        for line in f:
            # Process line
            process_line(line)
            processed += 1

            # Update progress every 100 lines
            if processed % 100 == 0:
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': processed,
                        'total': total_lines,
                        'status': f'Processing line {processed}/{total_lines}'
                    }
                )

    return {
        "status": "completed",
        "processed_lines": processed,
        "file_path": file_path
    }
```

## Task Organization

### Module Structure

Organize tasks by domain:

```
backend/app/tasks/
├── __init__.py
├── email_tasks.py      # Email-related tasks
├── file_tasks.py       # File processing tasks
├── user_tasks.py       # User management tasks
├── report_tasks.py     # Report generation tasks
└── cleanup_tasks.py    # Maintenance tasks
```

### Task Registration

Register tasks in the Celery configuration:

```python
# backend/app/worker/config.py
include = [
    "app.tasks.email_tasks",
    "app.tasks.file_tasks",
    "app.tasks.user_tasks",
    "app.tasks.report_tasks",
    "app.tasks.cleanup_tasks",
]
```

## API Integration

### Creating Task Endpoints

Add endpoints to trigger tasks:

```python
# backend/app/api/v1/endpoints/email.py
from app.tasks.email_tasks import send_welcome_email
from fastapi import APIRouter, status

router = APIRouter()

@router.post("/send-welcome", status_code=status.HTTP_202_ACCEPTED)
async def trigger_welcome_email(user_id: int) -> dict:
    """Trigger welcome email task."""
    # Get user details
    user = await get_user(user_id)

    # Queue the task
    task = send_welcome_email.delay(user.email, user.name)

    return {
        "task_id": task.id,
        "message": "Welcome email queued",
        "status": "PENDING"
    }
```

### Task Status Endpoints

Allow clients to check task status:

```python
@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> dict:
    """Get task status and result."""
    result = AsyncResult(task_id, app=celery_app)

    if result.state == 'PENDING':
        return {"task_id": task_id, "status": "PENDING"}
    elif result.state == 'PROGRESS':
        return {
            "task_id": task_id,
            "status": "PROGRESS",
            "progress": result.info
        }
    elif result.successful():
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": result.result
        }
    else:
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "error": str(result.info)
        }
```

## Best Practices

### 1. Idempotency

Tasks should be safe to run multiple times:

```python
@task_with_db(name="create_user_profile")
async def create_user_profile(db: AsyncSession, user_id: int) -> dict:
    """Create user profile (idempotent)."""
    # Check if profile already exists
    existing = await db.get(UserProfile, user_id)
    if existing:
        return {"status": "already_exists", "profile_id": existing.id}

    # Create new profile
    profile = UserProfile(user_id=user_id)
    db.add(profile)
    await db.commit()

    return {"status": "created", "profile_id": profile.id}
```

### 2. Input Validation

Validate all task inputs:

```python
@celery_app.task(name="send_notification")
def send_notification(user_id: int, message: str) -> dict:
    """Send notification with input validation."""
    # Validate inputs
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user_id")

    if not message or not isinstance(message, str):
        raise ValueError("Message is required and must be a string")

    if len(message) > 1000:
        raise ValueError("Message too long (max 1000 characters)")

    # Process notification
    return send_user_notification(user_id, message)
```

### 3. Timeouts

Set appropriate time limits:

```python
@celery_app.task(
    name="generate_report",
    time_limit=300,  # 5 minutes hard limit
    soft_time_limit=240  # 4 minutes soft limit
)
def generate_report(report_type: str) -> dict:
    """Generate report with timeout protection."""
    try:
        return create_report(report_type)
    except SoftTimeLimitExceeded:
        # Cleanup and return partial result
        logger.warning("Report generation taking too long, returning partial result")
        return {"status": "partial", "message": "Report generation timed out"}
```

### 4. Logging

Log important events and errors:

```python
import logging
from app.core.logging import get_logger

logger = get_logger(__name__)

@celery_app.task(name="process_order")
def process_order(order_id: str) -> dict:
    """Process order with comprehensive logging."""
    logger.info(f"Starting order processing: {order_id}")

    try:
        # Process order
        result = process_order_logic(order_id)
        logger.info(f"Order processed successfully: {order_id}")
        return result
    except Exception as e:
        logger.error(f"Order processing failed: {order_id}, error: {e}")
        raise
```

### 5. Resource Management

Clean up resources properly:

```python
@celery_app.task(name="process_file")
def process_file(file_path: str) -> dict:
    """Process file with proper resource cleanup."""
    temp_files = []

    try:
        # Create temporary files
        temp_file = create_temp_file()
        temp_files.append(temp_file)

        # Process file
        result = process_file_logic(file_path, temp_file)
        return result

    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
```

## Testing

### Unit Testing Tasks

Test task logic in isolation:

```python
# backend/app/tests/test_email_tasks.py
import pytest
from app.tasks.email_tasks import send_welcome_email

class TestEmailTasks:
    """Test email task functionality."""

    def test_send_welcome_email_success(self, mock_email_service):
        """Test successful email sending."""
        # Mock email service
        mock_email_service.send.return_value = {"status": "sent"}

        # Execute task synchronously
        result = send_welcome_email.apply(
            args=["user@example.com", "John Doe"],
            throw=True
        )

        # Verify result
        assert result.successful()
        assert result.result["status"] == "sent"
        assert result.result["recipient"] == "user@example.com"

    def test_send_welcome_email_invalid_email(self):
        """Test email task with invalid email."""
        with pytest.raises(ValueError, match="Invalid email"):
            send_welcome_email.apply(
                args=["invalid-email", "John Doe"],
                throw=True
            )
```

### Integration Testing

Test task integration with database:

```python
@pytest.mark.asyncio
class TestDatabaseTasks:
    """Test database-aware tasks."""

    async def test_update_user_stats(self, mock_db_session):
        """Test user stats update task."""
        # Setup mock user
        mock_user = User(id=1, email="test@example.com", login_count=5)
        mock_db_session.get.return_value = mock_user

        # Execute task
        result = await update_user_stats.run_with_db(mock_db_session, 1)

        # Verify result
        assert result["user_id"] == 1
        assert result["login_count"] == 6

        # Verify database calls
        mock_db_session.get.assert_called_once_with(User, 1)
        mock_db_session.commit.assert_called_once()
```

## Monitoring and Debugging

### Flower Monitoring

Start Flower for web-based monitoring:

```bash
just flower
# Visit http://localhost:5555
```

Flower provides:

- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Queue management

### Command Line Monitoring

Use Celery's built-in monitoring commands:

```bash
# Check worker status
just worker-status

# Monitor task events in real-time
cd backend && celery -A app.worker.celery_app events

# Inspect active tasks
cd backend && celery -A app.worker.celery_app inspect active

# View registered tasks
cd backend && celery -A app.worker.celery_app inspect registered
```

### Logging Configuration

Configure structured logging for tasks:

```python
# backend/app/worker/config.py
import logging

# Celery logging configuration
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Configure loggers
logging.getLogger('celery').setLevel(logging.INFO)
logging.getLogger('celery.task').setLevel(logging.INFO)
logging.getLogger('celery.worker').setLevel(logging.INFO)
```

## Production Deployment

### Docker Configuration

The production setup includes optimized configurations:

```yaml
# docker-compose.prod.yml
worker:
  deploy:
    replicas: 1 # Adjust based on workload
    resources:
      limits:
        memory: 512M
      reservations:
        memory: 256M
  restart: unless-stopped
```

### Redis Configuration

Production Redis includes:

```bash
# Redis optimizations
redis-server \
  --appendonly yes \
  --maxmemory 512mb \
  --maxmemory-policy allkeys-lru
```

### Worker Configuration

Production worker optimizations:

```bash
# docker/production/start-celeryworker.sh
celery -A app.worker.celery_app worker \
  --loglevel=warning \
  --concurrency=4 \
  --pool=prefork \
  --prefetch-multiplier=1 \
  --max-tasks-per-child=1000 \
  --without-heartbeat \
  --without-gossip \
  --without-mingle
```

### Monitoring in Production

Set up monitoring and alerting:

1. **Health Checks**: Monitor worker health
2. **Queue Monitoring**: Alert on queue length
3. **Error Tracking**: Monitor failed tasks
4. **Performance Metrics**: Track task execution times

### Scaling Considerations

- **Horizontal Scaling**: Add more worker instances
- **Queue Routing**: Route different task types to specific workers
- **Priority Queues**: Handle urgent tasks first
- **Resource Limits**: Set memory and CPU limits

## Troubleshooting

### Common Issues

**Tasks not executing:**

- Check Redis connection
- Verify worker is running
- Ensure tasks are properly registered

**Database connection errors:**

- Check database connectivity
- Verify connection pool settings
- Review async session configuration

**Memory issues:**

- Monitor worker memory usage
- Adjust `max-tasks-per-child` setting
- Review task resource usage

**Task timeouts:**

- Increase time limits for long-running tasks
- Implement progress reporting
- Consider task chunking

### Debugging Tips

1. **Use synchronous execution** for debugging:

   ```python
   # Execute task synchronously
   result = my_task.apply(args=[arg1, arg2], throw=True)
   ```

2. **Enable debug logging**:

   ```python
   import logging
   logging.getLogger('celery').setLevel(logging.DEBUG)
   ```

3. **Check task registration**:

   ```bash
   cd backend && celery -A app.worker.celery_app inspect registered
   ```

4. **Monitor task events**:
   ```bash
   cd backend && celery -A app.worker.celery_app events
   ```

## Advanced Patterns

### Task Chains

Chain tasks together:

```python
from celery import chain

# Create task chain
workflow = chain(
    preprocess_data.s(data_id),
    analyze_data.s(),
    generate_report.s(),
    send_notification.s()
)

# Execute chain
result = workflow.apply_async()
```

### Task Groups

Execute tasks in parallel:

```python
from celery import group

# Create task group
job = group(
    process_file.s(file_path)
    for file_path in file_paths
)

# Execute group
result = job.apply_async()
```

### Periodic Tasks

For scheduled tasks (requires Celery Beat):

```python
from celery.schedules import crontab

# In worker/config.py
beat_schedule = {
    'cleanup-old-files': {
        'task': 'app.tasks.cleanup_tasks.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
```

## Summary

This guide covers the essential aspects of developing background tasks with Celery and Redis. Key takeaways:

- Use appropriate task patterns for your use case
- Implement proper error handling and retries
- Follow best practices for idempotency and validation
- Monitor and debug tasks effectively
- Configure production deployments for scalability

For additional help, refer to the [Celery documentation](https://docs.celeryq.dev/) and the Reactrine examples.
