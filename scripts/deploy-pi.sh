#!/bin/bash

# Raspberry Pi Deployment Script
# This script deploys the application on a vanilla host using only Docker

set -e  # Exit on any error

echo "🚀 Deploying Reactrine on Raspberry Pi..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Docker is available
if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command_exists docker || ! docker compose version >/dev/null 2>&1; then
    echo "❌ Docker Compose is not available. Please install Docker Compose first."
    exit 1
fi

echo "🛑 Stopping and removing existing containers..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null || true

# echo "🧹 Cleaning up old images and build cache..."
# docker system prune -f --volumes

echo "🔄 Pulling latest changes from git..."
git pull --rebase

echo "🔐 Setting up secrets for production deployment..."
./scripts/setup-secrets.sh

echo "🌐 Detecting host IP address..."
HOST_IP=$(hostname -I | awk '{print $1}')
if [ -z "$HOST_IP" ]; then
    HOST_IP=$(ip route get 1.1.1.1 | awk '{print $7; exit}')
fi
if [ -z "$HOST_IP" ]; then
    echo "❌ Could not detect host IP address. Please set it manually."
    exit 1
fi
echo "   Detected host IP: $HOST_IP"

echo "⚙️ Updating TRUSTED_HOSTS_STR in prod.env with host IP..."
# Check if HOST_IP is already in TRUSTED_HOSTS_STR
if ! grep -q "TRUSTED_HOSTS_STR.*$HOST_IP" config/prod.env; then
    # Get current TRUSTED_HOSTS_STR value
    CURRENT_HOSTS=$(grep "^TRUSTED_HOSTS_STR=" config/prod.env | cut -d'=' -f2)
    if [ -z "$CURRENT_HOSTS" ] || [ "$CURRENT_HOSTS" = "localhost" ]; then
        # Replace with host IP
        sed -i "s/^TRUSTED_HOSTS_STR=.*/TRUSTED_HOSTS_STR=$HOST_IP/" config/prod.env
    else
        # Add host IP to existing hosts
        NEW_HOSTS="$CURRENT_HOSTS,$HOST_IP"
        sed -i "s/^TRUSTED_HOSTS_STR=.*/TRUSTED_HOSTS_STR=$NEW_HOSTS/" config/prod.env
    fi
    echo "   Updated TRUSTED_HOSTS_STR to include $HOST_IP"
else
    echo "   Host IP $HOST_IP already present in TRUSTED_HOSTS_STR"
fi

echo "🔑 Generating RSA keypair for Personal API Keys (if they don't exist)..."
if [ ! -f secrets/pak_private_key.txt ]; then
    echo "Generating new RSA keypair for PAKs..."
    python scripts/generate-pak-keypair.py
else
    echo "RSA keypair already exists, skipping generation."
fi

echo "🔐 Generating self-signed certificates (if they don't exist)..."
if [ ! -f docker/production/reverse-proxy/certs/privkey.pem ]; then
    echo "Generating self-signed certificates..."
    cd docker/production/reverse-proxy && chmod +x gen-certs.sh && ./gen-certs.sh && cd ../../..
else
    echo "SSL certificates already exist, skipping generation."
fi

echo "🏗️ Building production Docker images..."
echo "   This includes API client generation during the frontend build process..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

echo "⚙️ Applying database migrations..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm backend alembic upgrade head

echo "🚀 Starting application stack..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "⏳ Waiting for services to be healthy..."
# Wait for services to be ready
TIMEOUT=120
COUNTER=0
while [ $COUNTER -lt $TIMEOUT ]; do
    if docker compose -f docker-compose.yml -f docker-compose.prod.yml ps --filter "status=running" | grep -q backend && \
       docker compose -f docker-compose.yml -f docker-compose.prod.yml ps --filter "status=running" | grep -q frontend; then
        echo "✅ Services are running!"
        break
    fi
    echo "Waiting for services to start... ($COUNTER/$TIMEOUT seconds)"
    sleep 2
    COUNTER=$((COUNTER + 2))
done

if [ $COUNTER -ge $TIMEOUT ]; then
    echo "❌ Services failed to start within 120 seconds"
    echo "📋 Container status:"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
    echo "📋 Recent logs:"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=20
    exit 1
fi

echo "✅ Deployment complete! Application is running."
echo ""
echo "📋 Quick status check:"
echo "   Frontend: https://$HOST_IP"
echo "   Backend API: https://$HOST_IP/api/v1/health"
echo ""
echo "💡 Useful commands:"
echo "   View logs: docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
echo "   Stop services: docker compose -f docker-compose.yml -f docker-compose.prod.yml down"
echo "   Restart services: docker compose -f docker-compose.yml -f docker-compose.prod.yml restart"
echo "   Check status: docker compose -f docker-compose.yml -f docker-compose.prod.yml ps"
