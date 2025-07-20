# syntax=docker/dockerfile:1.7

# Stage 1: Build backend for OpenAPI spec generation
FROM python:3.12-slim as backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy OpenAPI generation script and run it
COPY scripts/generate-openapi-spec.py /tmp/generate-openapi-spec.py
RUN python /tmp/generate-openapi-spec.py

# Stage 2: Build frontend with generated API client
FROM node:20-alpine as frontend-builder

WORKDIR /app

# Copy OpenAPI spec from backend builder
COPY --from=backend-builder /tmp/openapi.json /tmp/openapi.json

# Install dependencies first (better caching)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source
COPY frontend/ .

# Generate API client from the OpenAPI spec file
RUN npx openapi --input /tmp/openapi.json --output ./src/lib/api-client --client axios --useOptions --useUnionTypes --exportSchemas true

# Build the frontend
RUN npm run build

# Stage 3: Production stage with nginx
FROM nginx:alpine

# Copy built assets from frontend builder stage
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY docker/production/nginx.conf /etc/nginx/nginx.conf

# Create non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
RUN chown -R appuser:appgroup /usr/share/nginx/html
RUN chown -R appuser:appgroup /var/cache/nginx
RUN chown -R appuser:appgroup /var/log/nginx
RUN chown -R appuser:appgroup /etc/nginx/conf.d
RUN touch /var/run/nginx.pid
RUN chown -R appuser:appgroup /var/run/nginx.pid

USER appuser

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
