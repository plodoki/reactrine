from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rbac import AdminOnly
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.llm_settings import (
    LLMSettingsCreateSchema,
    LLMSettingsSchema,
    LLMSettingsUpdateSchema,
)
from app.services.llm_settings import LLMSettingsService, get_llm_settings_service

router = APIRouter()


@router.get("/llm-settings", response_model=LLMSettingsSchema, tags=["LLM"])
async def get_llm_settings(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(AdminOnly),
    service: LLMSettingsService = Depends(get_llm_settings_service),
) -> LLMSettingsSchema:
    """Get current LLM settings. Requires admin role."""
    return await service.get_settings(db)


@router.post("/llm-settings", response_model=LLMSettingsSchema, tags=["LLM"])
async def create_llm_settings(
    payload: LLMSettingsCreateSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(AdminOnly),
    service: LLMSettingsService = Depends(get_llm_settings_service),
) -> LLMSettingsSchema:
    """Create new LLM settings. Requires admin role."""
    return await service.create_llm_settings(payload, db)


@router.patch("/llm-settings", response_model=LLMSettingsSchema, tags=["LLM"])
async def update_llm_settings(
    payload: LLMSettingsUpdateSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(AdminOnly),
    service: LLMSettingsService = Depends(get_llm_settings_service),
) -> LLMSettingsSchema:
    """Update existing LLM settings. Requires admin role."""
    return await service.update_llm_settings(payload, db)


@router.get("/llm-settings/lmstudio/models", response_model=list[str], tags=["LLM"])
async def get_lmstudio_models(
    current_user: User = Depends(AdminOnly),
    service: LLMSettingsService = Depends(get_llm_settings_service),
) -> list[str]:
    """Get available models from LMStudio server. Requires admin role."""
    return await service.get_lmstudio_models()
