from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.assets.storage import ObjectStore, get_object_store
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.talent.models import ModelProfile, ModelReferenceView
from aiimage.talent.schemas import (
    ModelProfileCreate,
    ModelProfileResponse,
    ModelReferenceResponse,
)
from aiimage.talent.service import (
    ModelProfileValidationError,
    add_model_reference,
    create_model_profile,
    model_profile_response,
)

router = APIRouter(prefix="/model-profiles", tags=["model-profiles"])
TalentUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.OPERATOR, Role.DESIGNER))]


@router.get("", response_model=list[ModelProfileResponse])
async def list_model_profiles(
    user: TalentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ModelProfileResponse]:
    del user
    profiles = list(
        (await session.scalars(select(ModelProfile).order_by(ModelProfile.created_at.desc()))).all()
    )
    return [await model_profile_response(session, profile) for profile in profiles]


@router.get("/{profile_id}", response_model=ModelProfileResponse)
async def get_model_profile(
    profile_id: UUID,
    user: TalentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ModelProfileResponse:
    del user
    profile = await session.get(ModelProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Model profile not found")
    return await model_profile_response(session, profile)


@router.post("", response_model=ModelProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_model_profile_endpoint(
    payload: ModelProfileCreate,
    user: TalentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ModelProfileResponse:
    try:
        profile = await create_model_profile(session, payload=payload, user_id=user.id)
    except ModelProfileValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return await model_profile_response(session, profile)


@router.post(
    "/{profile_id}/references",
    response_model=ModelReferenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_model_reference(
    profile_id: UUID,
    user: TalentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[ObjectStore, Depends(get_object_store)],
    view: Annotated[ModelReferenceView, Form()],
    file: Annotated[UploadFile, File()],
) -> ModelReferenceResponse:
    del user
    try:
        reference, asset = await add_model_reference(
            session,
            store,
            profile_id=profile_id,
            view=view,
            content=await file.read(),
            mime_type=file.content_type or "application/octet-stream",
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Model profile not found") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return ModelReferenceResponse(
        id=reference.id,
        asset_id=asset.id,
        view=reference.view,
        sha256=asset.sha256,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
    )
