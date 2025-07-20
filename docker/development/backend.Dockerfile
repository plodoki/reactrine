# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .

# Use BuildKit secrets for any private pip repositories
# The secret will be mounted at /run/secrets/pip_extra_index_url if provided
RUN --mount=type=secret,id=pip_extra_index_url,required=false \
    if [ -f /run/secrets/pip_extra_index_url ] && [ -s /run/secrets/pip_extra_index_url ]; then \
    EXTRA_INDEX_URL=$(cat /run/secrets/pip_extra_index_url) && \
    pip install --no-cache-dir --extra-index-url "$EXTRA_INDEX_URL" -r requirements.txt; \
    else \
    pip install --no-cache-dir -r requirements.txt; \
    fi

# Copy application code
COPY backend/ .

# Copy worker startup script
COPY docker/development/start-celeryworker.sh /start-celeryworker.sh
RUN chmod +x /start-celeryworker.sh

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
RUN chown appuser:appuser /start-celeryworker.sh
USER appuser

EXPOSE 8000

# Use --reload flag for auto-reloading during development
# Disable access logging to reduce noise, keep error logging
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--no-access-log"]
