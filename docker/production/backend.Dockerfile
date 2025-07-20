# syntax=docker/dockerfile:1.7
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .

# Use BuildKit secrets for any private pip repositories
RUN --mount=type=secret,id=pip_extra_index_url,required=false \
    if [ -f /run/secrets/pip_extra_index_url ] && [ -s /run/secrets/pip_extra_index_url ]; then \
    EXTRA_INDEX_URL=$(cat /run/secrets/pip_extra_index_url) && \
    pip install --no-cache-dir --user --extra-index-url "$EXTRA_INDEX_URL" -r requirements.txt; \
    else \
    pip install --no-cache-dir --user -r requirements.txt; \
    fi

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Copy Python packages from builder to appuser's local directory
COPY --from=builder /root/.local /home/appuser/.local
RUN chown -R appuser:appuser /home/appuser/.local

# Copy application code
COPY backend/ .

# Copy worker startup script
COPY docker/production/start-celeryworker.sh /start-celeryworker.sh
RUN chmod +x /start-celeryworker.sh

RUN chown -R appuser:appuser /app
RUN chown appuser:appuser /start-celeryworker.sh

USER appuser

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Production command (no reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
