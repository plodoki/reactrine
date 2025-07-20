#!/usr/bin/env python3
"""
Generate OpenAPI specification from FastAPI app.
This script is used during Docker builds to extract the OpenAPI spec
without needing to run a full server.
"""

import json
import os
import sys

# Set minimal environment variables required for FastAPI app initialization
os.environ.setdefault("ENVIRONMENT", "test")  # Enables default test secrets
os.environ.setdefault(
    "SECRET_KEY", "openapi-generation-secret-key"
)  # Direct secret for OpenAPI gen
os.environ.setdefault(
    "SESSION_SECRET_KEY", "openapi-generation-session-secret"
)  # Direct secret for OpenAPI gen
os.environ.setdefault(
    "DATABASE_URL", "postgresql://dummy:dummy@dummy:5432/dummy"
)  # Dummy DB URL (won't be used)
os.environ.setdefault("REDIS_URL", "redis://dummy:6379")  # Dummy Redis for OpenAPI gen

# Add the current directory to Python path so we can import the app
sys.path.insert(0, "/app")

try:
    from fastapi.openapi.utils import get_openapi

    from app.main import app

    # Generate OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Write to specified output file
    output_file = os.environ.get("OPENAPI_OUTPUT_FILE", "/tmp/openapi.json")
    with open(output_file, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"✅ OpenAPI spec generated successfully: {output_file}")

except Exception as e:
    print(f"❌ Failed to generate OpenAPI spec: {e}")
    sys.exit(1)
