
# Database Schema Management

This project uses Alembic for managing database schema changes with SQLModel/SQLAlchemy. The system supports both development and production environments with proper secret management.

## Prerequisites

-   Database credentials configured in `secrets/postgres_password.txt`
-   Development environment running (`just start`)
-   Your models are defined in `backend/app/models/` and imported in `backend/app/db/base.py` for Alembic to detect them.

## Development Workflow

### 1. Adding or Modifying Models

When you create or modify your SQLModel classes:

1.  **Define your model** in a file within `backend/app/models/`, for example:

    ```python
    # backend/app/models/your_model.py
    from sqlmodel import Field, SQLModel

    class YourModel(SQLModel, table=True):
        id: int | None = Field(default=None, primary_key=True)
        name: str = Field(index=True)
        description: str | None = None
    ```

2.  **Register the model** in `backend/app/models/__init__.py` so it can be easily imported elsewhere:

    ```python
    # In backend/app/models/__init__.py
    from .your_model import YourModel

    __all__ = ["LLMSettings", "User", "Role", "YourModel"] # Add YourModel here
    ```

3.  **Import the model in `base.py`** to ensure Alembic's autogenerate feature detects it:
    ```python
    # In backend/app/db/base.py
    from app.models.your_model import YourModel  # noqa: F401
    ```

### 2. Generating Migrations

Use the provided `just` command for a streamlined workflow. This command will automatically generate a migration file based on the changes it detects in your models.

```bash
# Generate a new migration based on model changes
just db-migrate
```

Alembic will generate a new migration script in `backend/alembic/versions/`. It's a good practice to review this file to ensure it accurately reflects the changes you intended to make.

### 3. Applying Migrations

To apply all pending migrations to your database, run:

```bash
# Apply all pending migrations
just db-upgrade
```

This brings your database schema up to date with your models.

### 4. Checking Migration Status

You can use the standard Alembic commands to inspect the state of your database migrations. You'll need to run them from the `backend` directory.

-   `alembic current`: Show the current migration version of the database.
-   `alembic history`: View the full history of all migrations.
-   `alembic show head`: See the details of the latest migration.

## Migration Commands Reference

| Command | Purpose | Example |
|---|---|---|
| `just db-migrate` | Generate new migration | `just db-migrate` |
| `just db-upgrade` | Apply pending migrations | `just db-upgrade` |
| `alembic current` | Show current version | `cd backend && alembic current` |
| `alembic history` | Show migration history | `cd backend && alembic history` |
| `alembic upgrade head` | Apply all migrations | `cd backend && alembic upgrade head` |
| `alembic upgrade +1` | Apply the next migration | `cd backend && alembic upgrade +1` |
| `alembic downgrade -1` | Rollback one migration | `cd backend && alembic downgrade -1` |
| `alembic downgrade <rev>` | Rollback to a specific version | `cd backend && alembic downgrade abc123`|

## Advanced Scenarios

### Manual Migrations

For complex schema changes that `autogenerate` can't handle (e.g., changing a column type that requires a data conversion), you can create an empty migration file and write the migration logic yourself.

```bash
# Create an empty migration file from the backend directory
cd backend
alembic revision -m "Your custom migration description"

# Edit the generated file manually in backend/alembic/versions/
```

### Data Migrations

For migrations that need to modify existing data, you can use `op.get_bind()` to get a database connection and execute SQL within your migration file.

```python
# In your migration file's upgrade() function
from sqlalchemy.sql import text

def upgrade() -> None:
    # Example: Add a 'full_name' column to the 'users' table
    op.add_column('users', sa.Column('full_name', sa.String(), nullable=True))

    # Now, populate the new column by combining 'first_name' and 'last_name'
    connection = op.get_bind()
    result = connection.execute(text("SELECT id, first_name, last_name FROM users"))

    for row in result:
        full_name = f"{row.first_name} {row.last_name}"
        connection.execute(
            text("UPDATE users SET full_name = :full_name WHERE id = :id"),
            {"full_name": full_name, "id": row.id}
        )

    # After the data migration, you can make the column non-nullable if desired
    op.alter_column('users', 'full_name', nullable=False)
```

## Best Practices

#### ✅ DO:

-   Always review generated migrations before applying them.
-   Test migrations on a development or staging database first.
-   Backup your production database before running migrations.
-   Use descriptive names for your migration files when creating them manually.
-   Commit your migration files to version control.

#### ❌ DON'T:

-   Edit migration files that have already been applied to a shared database (e.g., `main` or `production`). If you need to make a change, create a new migration.
-   Run migrations in production without a backup and a rollback plan.
-   Delete migration files that have been applied.
-   Modify models without generating a corresponding migration.
