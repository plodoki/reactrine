"""Service for managing roles with comprehensive business logic."""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.role import Role
from app.repositories.role import RoleRepository
from app.utils.error_handling import with_database_error_handling

logger = get_logger(__name__)


class RoleService:
    """Service for handling role operations with business logic."""

    def __init__(self) -> None:
        """Initialize role service."""
        self.role_repo = RoleRepository()

    @with_database_error_handling("get role by name")
    async def get_role_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        """
        Get a role by name.

        Args:
            db: Database session
            name: Role name

        Returns:
            Role if found, None otherwise
        """
        result: Optional[Role] = await self.role_repo.get_by_name(db, name)
        return result

    @with_database_error_handling("get all roles")
    async def get_all_roles(self, db: AsyncSession) -> List[Role]:
        """
        Get all available roles.

        Args:
            db: Database session

        Returns:
            List of all roles
        """
        result: List[Role] = await self.role_repo.get_all_active(db)
        return result

    @with_database_error_handling("check role existence")
    async def role_exists(self, db: AsyncSession, name: str) -> bool:
        """
        Check if a role exists.

        Args:
            db: Database session
            name: Role name

        Returns:
            True if role exists, False otherwise
        """
        result: bool = await self.role_repo.name_exists(db, name)
        return result

    async def ensure_default_roles(self, db: AsyncSession) -> None:
        """
        Ensure default roles exist in the database.

        Args:
            db: Database session
        """
        default_roles = [
            ("admin", "Administrator with full system access"),
            ("user", "Standard user with basic access"),
        ]

        for role_name, description in default_roles:
            if not await self.role_exists(db, role_name):
                logger.info(f"Creating default role: {role_name}")
                role = Role(name=role_name, description=description)
                await self.role_repo.create(db, role)


# Service instance for dependency injection
role_service = RoleService()


def get_role_service() -> RoleService:
    """Dependency injection function for role service."""
    return role_service
