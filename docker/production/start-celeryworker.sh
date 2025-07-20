#!/bin/bash
set -e

echo "🚀 Starting Celery worker (production)..."

# Wait for services to be ready
echo "⏳ Waiting for Redis to be ready..."
until python -c "
import redis
import os
# Use environment variable or default Redis URL for health check
redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
try:
    r = redis.from_url(redis_url)
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
"; do
  echo "Redis is unavailable - sleeping"
  sleep 1
done
echo "✅ Redis is ready!"

echo "⏳ Waiting for database to be ready..."
until python -c "
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_db():
    # Construct database URL from environment variables
    postgres_server = os.getenv('POSTGRES_SERVER', 'postgres')
    postgres_user = os.getenv('POSTGRES_USER', 'postgres')
    postgres_db = os.getenv('POSTGRES_DB', 'app')

    # Read password from secrets file (Docker secrets)
    try:
        with open('/run/secrets/postgres_password', 'r') as f:
            postgres_password = f.read().strip()
    except FileNotFoundError:
        # Fallback to environment variable for local development
        postgres_password = os.getenv('POSTGRES_PASSWORD', 'password')

    db_url = f'postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_server}:5432/{postgres_db}'

    engine = create_async_engine(db_url)
    async with engine.connect() as conn:
        await conn.execute(text('SELECT 1'))
    await engine.dispose()

asyncio.run(check_db())
"; do
  echo "Database is unavailable - sleeping"
  sleep 1
done
echo "✅ Database is ready!"

# Production-optimized worker settings
exec celery -A app.worker.celery_app worker \
  --loglevel=warning \
  --concurrency=4 \
  --pool=prefork \
  --prefetch-multiplier=1 \
  --max-tasks-per-child=1000 \
  --without-heartbeat \
  --without-gossip \
  --without-mingle
