from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore
from aiimage.talent.models import (
    AuthorizationStatus,
    ModelProfile,
    ModelProfileType,
    ModelReference,
    ModelReferenceView,
)
from aiimage.talent.schemas import (
    ModelProfileCreate,
    ModelProfileResponse,
    ModelReferenceResponse,
)


class ModelProfileValidationError(ValueError):
    pass


def validate_authorization(payload: ModelProfileCreate, *, today: date | None = None) -> None:
    current = today or datetime.now(UTC).date()
    if payload.profile_type == ModelProfileType.SYSTEM_VIRTUAL:
        if payload.authorization_status != AuthorizationStatus.NOT_REQUIRED:
            raise ModelProfileValidationError("System virtual models use not_required authorization")
        if payload.authorization_expires_on is not None:
            raise ModelProfileValidationError("System virtual models do not have authorization expiry")
        return
    if payload.authorization_status == AuthorizationStatus.NOT_REQUIRED:
        raise ModelProfileValidationError("Brand models require explicit authorization")
    if payload.authorization_expires_on is None:
        raise ModelProfileValidationError("Brand models require authorization expiry")
    if (
        payload.authorization_status == AuthorizationStatus.VALID
        and payload.authorization_expires_on < current
    ):
        raise ModelProfileValidationError("Valid authorization cannot already be expired")


def authorization_is_current(profile: ModelProfile, *, today: date | None = None) -> bool:
    if not profile.is_active:
        return False
    if profile.profile_type == ModelProfileType.SYSTEM_VIRTUAL.value:
        return profile.authorization_status == AuthorizationStatus.NOT_REQUIRED.value
    current = today or datetime.now(UTC).date()
    return (
        profile.authorization_status == AuthorizationStatus.VALID.value
        and profile.authorization_expires_on is not None
        and profile.authorization_expires_on >= current
    )


async def create_model_profile(
    session: AsyncSession, *, payload: ModelProfileCreate, user_id: UUID
) -> ModelProfile:
    validate_authorization(payload)
    profile = ModelProfile(
        name=payload.name.strip(),
        profile_type=payload.profile_type.value,
        authorization_status=payload.authorization_status.value,
        authorization_expires_on=payload.authorization_expires_on,
        attributes=payload.attributes,
        created_by_user_id=user_id,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


async def add_model_reference(
    session: AsyncSession,
    store: ObjectStore,
    *,
    profile_id: UUID,
    view: ModelReferenceView,
    content: bytes,
    mime_type: str,
) -> tuple[ModelReference, Asset]:
    if await session.get(ModelProfile, profile_id) is None:
        raise LookupError(profile_id)
    stored = await store.put(content=content, mime_type=mime_type)
    asset = await session.scalar(select(Asset).where(Asset.sha256 == stored.sha256))
    if asset is None:
        asset = Asset(
            object_key=stored.object_key,
            sha256=stored.sha256,
            size_bytes=stored.size_bytes,
            mime_type=stored.mime_type,
        )
        session.add(asset)
        await session.flush()
    reference = ModelReference(profile_id=profile_id, asset_id=asset.id, view=view.value)
    session.add(reference)
    await session.commit()
    return reference, asset


async def model_profile_response(
    session: AsyncSession, profile: ModelProfile
) -> ModelProfileResponse:
    references = list(
        (
            await session.scalars(
                select(ModelReference).where(ModelReference.profile_id == profile.id)
            )
        ).all()
    )
    assets = {
        asset.id: asset
        for asset in (
            await session.scalars(
                select(Asset).where(Asset.id.in_([reference.asset_id for reference in references]))
            )
        ).all()
    }
    return ModelProfileResponse(
        id=profile.id,
        name=profile.name,
        profile_type=profile.profile_type,
        authorization_status=profile.authorization_status,
        authorization_expires_on=profile.authorization_expires_on,
        attributes=profile.attributes,
        is_active=profile.is_active,
        is_selectable=authorization_is_current(profile) and bool(references),
        created_at=profile.created_at,
        references=[
            ModelReferenceResponse(
                id=reference.id,
                asset_id=reference.asset_id,
                view=reference.view,
                sha256=assets[reference.asset_id].sha256,
                mime_type=assets[reference.asset_id].mime_type,
                size_bytes=assets[reference.asset_id].size_bytes,
            )
            for reference in references
        ],
    )
