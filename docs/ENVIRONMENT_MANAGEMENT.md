# Environment Management

This project follows a modern 4-plane environment management approach that separates:

1. **Build-time secrets** (BuildKit secrets)
2. **Runtime configuration** (env_file)
3. **Runtime secrets** (Docker/Compose secrets)
4. **Orchestration-level secrets** (external secret managers)

## Architecture Overview

```
┌─────────────────┬──────────────────┬─────────────────────┬──────────────────────┐
│ Build-time      │ Runtime Config   │ Runtime Secrets     │ Orchestration        │
├─────────────────┼──────────────────┼─────────────────────┼──────────────────────┤
│ BuildKit        │ env_file:        │ Docker secrets      │ External managers    │
│ secrets         │ environment:     │ /run/secrets/*      │ (Vault, AWS, etc.)   │
├─────────────────┼──────────────────┼─────────────────────┼──────────────────────┤
│ • Private repos │ • API URLs       │ • Database passwords│ • Production secrets │
│ • Build tokens  │ • Debug flags    │ • API keys          │ • Rotation & audit   │
│ • Certificates  │ • Log levels     │ • Certificates      │ • Compliance         │
└─────────────────┴──────────────────┴─────────────────────┴──────────────────────┘
```

## Directory Structure

```
├── config/                    # Runtime configuration (non-secret)
│   ├── common.env            # Shared across all environments
│   ├── dev.env               # Development overrides
│   └── prod.env              # Production overrides
├── secrets/                   # Runtime secrets (local development)
│   ├── .gitkeep              # Ensures directory exists in git
│   ├── *.txt.example         # Example secret files (committed)
│   └── *.txt                 # Actual secret files (ignored)
├── docker-compose.yml         # Development configuration
├── docker-compose.prod.yml    # Production configuration
└── scripts/setup-secrets.sh   # Setup script for local development
```

## Development Setup

### 1. Initial Setup

```bash
# Run the setup command (includes secret setup)
just setup

# Or manually setup secrets
./scripts/setup-secrets.sh
```

### 2. Configure Secrets

Edit the secret files in the `secrets/` directory:

```bash
# Database password
echo "your_postgres_password" > secrets/postgres_password.txt

# Application secret key (generate a secure one)
echo "$(openssl rand -base64 32)" > secrets/secret_key.txt

# API keys
echo "sk-your-openai-api-key" > secrets/openai_api_key.txt
echo "your-aws-access-key-id" > secrets/aws_access_key_id.txt
echo "your-aws-secret-access-key" > secrets/aws_secret_access_key.txt
```

### 3. Start Development Environment

```bash
just start
```

## Configuration Files

### config/common.env

Non-secret configuration shared across all environments:

```env
# Database Configuration (non-secret parts)
POSTGRES_SERVER=postgres
POSTGRES_USER=postgres
POSTGRES_DB=app

# API Configuration
API_V1_STR=/api/v1
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Logging
LOG_LEVEL=INFO
```

### config/dev.env

Development-specific overrides:

```env
# Environment
ENVIRONMENT=development
DEBUG=true

# CORS for local development
ALLOWED_ORIGINS_STR=http://localhost:3000,http://localhost:8000

# LLM Provider
# Options: openai, openrouter, bedrock
LLM_PROVIDER=openai
```

### config/prod.env

Production-specific overrides:

```env
# Environment
ENVIRONMENT=production
DEBUG=false

# CORS for production (update with your domains)
ALLOWED_ORIGINS_STR=https://yourdomain.com,https://api.yourdomain.com

# LLM Provider
# Options: openai, openrouter, bedrock
LLM_PROVIDER=bedrock
```

## Secrets Management

### Development (Local)

Secrets are stored in local files and mounted as Docker secrets:

```yaml
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

### Production

Secrets are managed externally and referenced by name:

```yaml
secrets:
  postgres_password:
    external: true
    name: Reactrine_postgres_password
  secret_key:
    external: true
    name: Reactrine_secret_key
```

## Production Deployment

### Docker Swarm

```bash
# Create secrets
echo "production_postgres_password" | docker secret create Reactrine_postgres_password -
echo "production_secret_key" | docker secret create Reactrine_secret_key -

# Deploy with production config
docker stack deploy -c docker-compose.prod.yml Reactrine
```

### Kubernetes

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: Reactrine-secrets
type: Opaque
data:
  postgres_password: <base64-encoded-password>
  secret_key: <base64-encoded-key>
```

### AWS ECS with Secrets Manager

```json
{
  "secrets": [
    {
      "name": "POSTGRES_PASSWORD",
      "valueFrom": "arn:aws:secretsmanager:region:account:secret:Reactrine/postgres-password"
    }
  ]
}
```

## BuildKit Secrets

For build-time secrets (like private repository access):

```dockerfile
# syntax=docker/dockerfile:1.7
RUN --mount=type=secret,id=pip_extra_index_url,required=false \
    if [ -f /run/secrets/pip_extra_index_url ]; then \
        pip install --extra-index-url "$(cat /run/secrets/pip_extra_index_url)" -r requirements.txt; \
    else \
        pip install -r requirements.txt; \
    fi
```

Build with secrets:

```bash
echo "https://user:token@private-pypi.com/simple/" | \
docker build --secret id=pip_extra_index_url,src=/dev/stdin .
```

## Security Best Practices

### ✅ DO

- Use Docker secrets for sensitive runtime values
- Keep non-secret config in `config/*.env` files
- Use external secret managers in production
- Rotate secrets regularly
- Use BuildKit secrets for build-time credentials
- Audit secret access and usage

### ❌ DON'T

- Put secrets in environment variables
- Commit secrets to version control
- Use the same secrets across environments
- Hardcode secrets in Dockerfiles
- Share secrets via insecure channels
- Use weak or default passwords

## Troubleshooting

### Secret Not Found

```bash
# Check if secret file exists
ls -la secrets/

# Check Docker secrets
docker secret ls

# Check container secret mounts
docker exec <container> ls -la /run/secrets/
```

### Environment Variable Not Set

```bash
# Check what variables are actually set
docker compose exec backend env | grep -E 'DATABASE|SECRET|API'

# Check config precedence
docker compose config --variables
```

### Build Secrets Not Working

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Check Dockerfile syntax
head -1 docker/*/Dockerfile  # Should show syntax=docker/dockerfile:1.7

# Build with verbose output
docker build --progress=plain .
```

## Migration from Old System

If migrating from the old `.env.development` approach:

1. **Extract secrets** from `.env.development` to `secrets/*.txt` files
2. **Move non-secret config** to `config/dev.env`
3. **Update docker-compose.yml** to use new structure
4. **Test the new setup** with `just start`
5. **Remove old files** once confirmed working

## CI/CD Integration

### GitHub Actions

```yaml
- name: Build with secrets
  run: |
    echo "${{ secrets.PIP_EXTRA_INDEX_URL }}" | \
    docker build --secret id=pip_extra_index_url,src=/dev/stdin .
```

### GitLab CI

```yaml
build:
  script:
    - echo "$PIP_EXTRA_INDEX_URL" | docker build --secret id=pip_extra_index_url,src=/dev/stdin .
```

## References

- [Docker BuildKit Secrets](https://docs.docker.com/build/building/secrets/)
- [Docker Compose Secrets](https://docs.docker.com/compose/use-secrets/)
- [12-Factor App Config](https://12factor.net/config)
- [OWASP Secrets Management](https://owasp.org/www-community/vulnerabilities/Insecure_Storage_of_Sensitive_Information)
