# syntax=docker/dockerfile:1.7
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (better caching)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

# Copy application code
COPY frontend/ .

# Use non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 3000

CMD ["npm", "run", "dev"]
