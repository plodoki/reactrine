# Docker Configuration

This directory contains the Docker configuration for the Reactrine project.

## Structure

```
docker/
├── development/
│   ├── backend.Dockerfile     # Development backend build
│   └── frontend.Dockerfile    # Development frontend build
├── production/
│   ├── backend.Dockerfile     # Production backend build (multi-stage)
│   ├── frontend.Dockerfile    # Production frontend build (multi-stage)
│   └── nginx.conf             # Production nginx configuration
└── README.md                  # This file
```

## Docker Compose Files

The project uses Docker Compose's override mechanism for environment-specific configuration:

### Base Configuration

- **`docker-compose.yml`** - Contains common configuration shared across all environments

### Development Configuration

- **`docker-compose.override.yml`** - Development-specific overrides (automatically loaded)
- Includes volume mounts for hot reloading
- Uses development Dockerfiles
- Exposes ports for local access

### Production Configuration

- **`docker-compose.prod.yml`** - Production-specific overrides
- Uses production Dockerfiles with multi-stage builds
- Configures resource limits
- Uses external secrets management

## Usage

### Development

```bash
# Standard development startup (automatically uses override file)
docker-compose up -d

# Rebuild and start
docker-compose up -d --build

# View logs
docker-compose logs -f
```

### Production

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Production with rebuild
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (development)
docker-compose down -v
```

## Benefits of This Structure

1. **DRY Principle** - Common configuration is defined once in the base file
2. **Environment Separation** - Clear separation between dev and prod concerns
3. **Docker Compose Standards** - Uses standard override mechanisms
4. **Maintainability** - Changes to common config only need to be made in one place
5. **Flexibility** - Easy to add new environments or modify existing ones

## Secrets Management

- **Development**: Uses local files in `secrets/` directory
- **Production**: Uses external secrets (managed by orchestration platform)

For more information on secrets setup, see the main project documentation.
