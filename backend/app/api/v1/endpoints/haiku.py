from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.haiku import HaikuRequest, HaikuResponse
from app.services.haiku import (
    get_haiku_service_default,
    get_haiku_service_with_overrides,
)

router = APIRouter()


@router.post(
    "/haiku",
    response_model=HaikuResponse,
    summary="Generate a Haiku",
    description="Generates a haiku based on a given topic and style, with optional LLM provider and model overrides.",
    tags=["Haiku"],
)
async def generate_haiku_endpoint(
    request: HaikuRequest, db: AsyncSession = Depends(get_db_session)
) -> HaikuResponse:
    """
    Endpoint to generate a haiku.

    - **topic**: The subject of the haiku.
    - **style**: The artistic style of the haiku (e.g., 'traditional', 'modern').
    - **provider**: Optional LLM provider override (e.g., 'openai', 'openrouter', 'bedrock').
    - **model**: Optional model override for the specified or default provider.
    """
    # Use the enhanced service if provider or model overrides are specified
    if request.provider or request.model:
        haiku_service = await get_haiku_service_with_overrides(
            provider=request.provider, model=request.model, db=db
        )
    else:
        # Use the standard service - we need to pass the db session for LLM service creation
        haiku_service = await get_haiku_service_default(db=db)

    return await haiku_service.generate_haiku(request)
