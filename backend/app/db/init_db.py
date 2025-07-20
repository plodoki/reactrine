"""
Database initialization functions.

This module provides functions to initialize the database with default data
that the application requires to function properly.
"""

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import LLMSettings

logger = get_logger(__name__)


async def init_default_llm_settings(db: AsyncSession) -> None:
    """
    Initialize default LLM settings if they don't exist.

    This function creates a default LLM settings record with id=1
    using the configuration from environment variables. Uses atomic
    operation to prevent race conditions during concurrent initialization.

    Args:
        db: Database session
    """
    try:
        # Get application settings
        app_settings = get_settings()

        # Create default LLM settings
        # Handle empty environment variables gracefully by using None for empty strings
        default_settings = LLMSettings(
            id=1,
            provider=app_settings.LLM_PROVIDER,
            openai_model=app_settings.DEFAULT_LLM_MODEL or None,
            openrouter_model=app_settings.OPENROUTER_MODEL or None,
            bedrock_model=app_settings.BEDROCK_MODEL or None,
            lmstudio_model=app_settings.LMSTUDIO_MODEL or None,
        )

        db.add(default_settings)

        try:
            await db.commit()
            await db.refresh(default_settings)
            logger.info(
                f"Created default LLM settings with provider: {app_settings.LLM_PROVIDER}"
            )
        except IntegrityError:
            # Another process/thread already created the record, rollback and continue
            await db.rollback()
            logger.info("LLM settings were created by another process, skipping")

    except SQLAlchemyError as e:
        logger.error(f"Database error initializing default LLM settings: {e}")
        await db.rollback()
        raise


async def init_roles_and_admin(db: AsyncSession) -> None:
    """
    Initialize default roles and promote initial admin user.

    Args:
        db: Database session
    """
    from app.services.role import get_role_service
    from app.services.user import assign_user_role, get_user_by_email_with_role

    role_service = get_role_service()
    settings = get_settings()

    # Ensure default roles exist
    await role_service.ensure_default_roles(db)

    # Promote initial admin user if configured
    if settings.INITIAL_ADMIN_EMAIL:
        try:
            user = await get_user_by_email_with_role(db, settings.INITIAL_ADMIN_EMAIL)
            if user and user.id is not None:
                # Check if user is already admin
                if user.role and user.role.name == "admin":
                    logger.info(f"User {settings.INITIAL_ADMIN_EMAIL} is already admin")
                else:
                    # Promote to admin
                    await assign_user_role(db, user.id, "admin")
                    logger.info(
                        f"Promoted user {settings.INITIAL_ADMIN_EMAIL} to admin"
                    )
            else:
                logger.warning(
                    f"Initial admin user {settings.INITIAL_ADMIN_EMAIL} not found. "
                    "User must register first before being promoted to admin."
                )
        except Exception as e:
            logger.error(f"Failed to promote initial admin user: {e}")


async def init_database(db: AsyncSession) -> None:
    """
    Initialize database with default data.

    This function should be called on application startup to ensure
    all required default data exists in the database.

    Args:
        db: Database session
    """
    logger.info("Initializing database with default data...")

    # Initialize default LLM settings
    await init_default_llm_settings(db)

    # Initialize roles and admin user
    await init_roles_and_admin(db)

    logger.info("Database initialization completed")
