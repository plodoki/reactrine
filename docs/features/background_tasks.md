# Background Tasks with Celery

The Reactrine includes a robust system for running background tasks using Celery and Redis. This allows you to execute long-running operations, such as sending emails, processing data, or calling slow third-party APIs, without blocking the main application thread or delaying API responses.

## Core Components

- **Celery:** A powerful, distributed task queue system.
- **Redis:** A fast, in-memory data store used as the message broker between your application and the Celery workers.
- **Celery Worker:** A separate process that listens for and executes background tasks.

## How It Works

1.  **Task Definition:** You define tasks as simple Python functions decorated with `@celery_app.task`.
2.  **Task Enqueueing:** When you want to run a task, you call its `.delay()` or `.apply_async()` method from your application code (e.g., in a FastAPI endpoint). This sends a message to the Redis message broker.
3.  **Task Execution:** The Celery worker, running as a separate process, picks up the message from Redis and executes the corresponding task function with the provided arguments.

This asynchronous workflow ensures that your API can respond to the user immediately, while the heavy lifting is handled in the background.

## Defining a New Task

Creating a new background task is straightforward:

1.  Create a new file in the `backend/app/tasks/` directory (e.g., `my_new_task.py`).
2.  Import the `celery_app` instance and define your function with the `@celery_app.task` decorator.

Here's an example of a simple task:

```python
# backend/app/tasks/example_task.py

from app.worker.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)

@celery_app.task
def send_welcome_email(user_id: int):
    """
    A background task to send a welcome email to a new user.
    """
    logger.info(f"Sending welcome email to user {user_id}...")
    # Add your email sending logic here
    # This can be a slow operation, but it won't block the API response.
    import time
    time.sleep(5) # Simulate a slow task
    logger.info(f"Successfully sent welcome email to user {user_id}.")
    return {"status": "success", "user_id": user_id}
```

## Triggering a Task

You can trigger a task from anywhere in your backend code, but it's most commonly done from within an API endpoint.

```python
# backend/app/api/v1/endpoints/auth.py

from app.tasks.example_task import send_welcome_email

@router.post("/register", response_model=UserRead)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
):
    # ... user creation logic ...

    # Enqueue the background task to send a welcome email
    send_welcome_email.delay(new_user.id)

    return new_user
```

## Running the Worker

The Celery worker is automatically started as part of the Docker Compose setup when you run `just start`. You can view its logs to monitor task execution:

```bash
just logs worker
```

If you are developing locally without Docker, you can start the worker manually:

```bash
just worker
```

This setup provides a scalable and reliable way to handle background processing, improving the responsiveness and robustness of your application.
