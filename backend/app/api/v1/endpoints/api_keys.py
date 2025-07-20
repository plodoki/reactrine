"""
API endpoints for Personal API Key management.

These endpoints allow users to create, list, and revoke their API keys.
All endpoints require valid session authentication (cookie + CSRF).
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyInfo,
    ApiKeyList,
    ApiKeyRevoked,
)
from app.services.api_key import ApiKeyService, get_api_key_service

router = APIRouter()

# Create limiter instance for rate limiting
limiter = Limiter(key_func=get_remote_address)

# Initialize logger
logger = get_logger(__name__)


@router.get("/", response_model=ApiKeyList, tags=["api-keys"])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ApiKeyService = Depends(get_api_key_service),
) -> ApiKeyList:
    """
    List all API keys for the current user.

    Returns all API keys (active and revoked) ordered by creation date.
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required",
        )
    result: ApiKeyList = await service.list_user_keys(db, current_user.id)
    return result


@router.post("/", response_model=ApiKeyCreated, tags=["api-keys"])
@limiter.limit("3/minute")
async def create_api_key(
    request: Request,
    api_key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ApiKeyService = Depends(get_api_key_service),
) -> ApiKeyCreated:
    """
    Create a new Personal API Key.

    The token is only returned once during creation and cannot be retrieved later.
    Rate limited to 3 requests per minute.
    """
    api_key, token = await service.create_api_key(
        db=db,
        user=current_user,
        label=api_key_data.label,
        expires_in_days=api_key_data.expires_in_days,
    )

    return ApiKeyCreated(api_key=ApiKeyInfo.model_validate(api_key), token=token)


@router.delete("/{key_id}", response_model=ApiKeyRevoked, tags=["api-keys"])
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ApiKeyService = Depends(get_api_key_service),
) -> ApiKeyRevoked:
    """
    Revoke an API key by ID.

    Only the owner of the API key can revoke it.
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required",
        )
    await service.revoke_user_key(db, key_id, current_user.id)
    return ApiKeyRevoked(success=True, message="API key revoked successfully")
