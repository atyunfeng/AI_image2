from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.audit.service import record_audit_event
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.config import Settings, get_settings
from aiimage.models.models import ModelConfiguration
from aiimage.models.schemas import ModelCreate, ModelResponse, ModelUpdate
from aiimage.models.service import (
    create_model_configuration,
    to_response,
    update_model_configuration,
)
from aiimage.providers.registry import ProviderRegistry

router = APIRouter(prefix="/models", tags=["models"])
AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]
ModelReader = Annotated[
    User,
    Depends(require_roles(Role.ADMIN, Role.OPERATOR, Role.DESIGNER)),
]


@router.get("", response_model=list[ModelResponse])
async def list_models(
    user: ModelReader,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ModelResponse]:
    del user
    models = list(
        (
            await session.scalars(
                select(ModelConfiguration)
                .order_by(ModelConfiguration.created_at.desc())
                .offset(offset)
                .limit(limit)
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


@router.patch("/{model_id}", response_model=ModelResponse)
async def update_model_endpoint(
    model_id: UUID,
    payload: ModelUpdate,
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ModelResponse:
    configuration = await session.get(ModelConfiguration, model_id)
    if configuration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    updated = await update_model_configuration(
        session,
        configuration=configuration,
        payload=payload,
        user=user,
    )
    return to_response(updated)


@router.post("/{model_id}/test")
async def test_model_connection(
    model_id: UUID,
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    configuration = await session.get(ModelConfiguration, model_id)
    if configuration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    try:
        await ProviderRegistry(
            secret_key_base64=settings.secret_key_base64,
            allow_private_urls=settings.allow_private_provider_urls,
        ).get(
            configuration
        ).test_connection()
    except Exception as error:
        await record_audit_event(
            session,
            event_type="model.connection_failed",
            actor_user_id=user.id,
            details={"model_configuration_id": str(configuration.id)},
        )
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Provider connection failed",
        ) from error
    await record_audit_event(
        session,
        event_type="model.connection_succeeded",
        actor_user_id=user.id,
        details={"model_configuration_id": str(configuration.id)},
    )
    await session.commit()
    return {"status": "ok"}
