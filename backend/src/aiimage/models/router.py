from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.config import Settings, get_settings
from aiimage.models.models import ModelConfiguration
from aiimage.models.schemas import ModelCreate, ModelResponse
from aiimage.models.service import create_model_configuration, to_response
from aiimage.providers.registry import ProviderRegistry

router = APIRouter(prefix="/models", tags=["models"])
AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]


@router.get("", response_model=list[ModelResponse])
async def list_models(
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ModelResponse]:
    del user
    models = list(
        (
            await session.scalars(
                select(ModelConfiguration).order_by(ModelConfiguration.created_at.desc())
            )
        ).all()
    )
    return [to_response(configuration) for configuration in models]


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model_endpoint(
    payload: ModelCreate,
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ModelResponse:
    configuration = await create_model_configuration(session, payload=payload, user=user)
    return to_response(configuration)


@router.post("/{model_id}/test")
async def test_model_connection(
    model_id: str,
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    del user
    configuration = await session.get(ModelConfiguration, model_id)
    if configuration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    try:
        await ProviderRegistry(secret_key_base64=settings.secret_key_base64).get(
            configuration
        ).test_connection()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Provider connection failed",
        ) from error
    return {"status": "ok"}
