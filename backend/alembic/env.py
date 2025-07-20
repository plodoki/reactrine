"""
Alembic migration environment.
"""

# Standard library imports
import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

# Third-party imports
from alembic import context

# Add the project root directory to the Python path just before local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Local application imports - must be after sys.path insertion
from app.core.logging import get_logger  # noqa
from app.db.base import SQLModel  # noqa - imports all models
from app.utils.secrets import read_secret  # noqa

logger = get_logger(__name__)
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for 'autogenerate'
target_metadata = SQLModel.metadata


def get_db_url() -> str:
    """
    Get the synchronous database URL suitable for Alembic.
    Reads environment variables and secrets using the new secret management system.
    """
    user = os.getenv("POSTGRES_USER", "postgres")
    password = read_secret("postgres_password") or "postgres"
    db = os.getenv("POSTGRES_DB", "app")

    # Determine server based on Docker environment
    # Check for /.dockerenv first, then fallback to POSTGRES_SERVER env var if set,
    # otherwise default to 'postgres' if in Docker, 'localhost' if not.
    is_in_docker = os.path.exists("/.dockerenv")
    server_env = os.getenv("POSTGRES_SERVER")

    if is_in_docker:
        # Inside Docker: use POSTGRES_SERVER env var or default to 'postgres'
        server = server_env or "postgres"
    else:
        # Outside Docker: if POSTGRES_SERVER is set to 'postgres' (Docker service name),
        # override it to 'localhost' since we're not in Docker
        if server_env == "postgres":
            server = "localhost"
        else:
            server = server_env or "localhost"

    # Construct the URL with the psycopg2 driver
    db_url = f"postgresql+psycopg2://{user}:{password}@{server}/{db}"

    return db_url


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    context.configure(
        url=get_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = create_engine(
        get_db_url(),
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
