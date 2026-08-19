from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.audit.service import record_audit_event
from aiimage.auth.models import User
from aiimage.config import get_settings
from aiimage.models.models import ModelConfiguration
from aiimage.models.schemas import ModelCreate, ModelResponse, ModelUpdate
from aiimage.models.secrets import SecretCipher


def to_response(configuration: ModelConfiguration) -> ModelResponse:
    return ModelResponse(
        id=configuration.id,
        name=configuration.name,
        provider=configuration.provider,
        model_id=configuration.model_id,
        base_url=configuration.base_url,
        billing_currency=configuration.billing_currency,
        provider_options=configuration.provider_options,
        capabilities=configuration.capabilities,
        has_key=configuration.encrypted_api_key is not None,
        key_suffix=configuration.key_suffix,
        is_enabled=configuration.is_enabled,
    )


async def create_model_configuration(
    session: AsyncSession,
    *,
    payload: ModelCreate,
    user: User,
) -> ModelConfiguration:
    ciphertext = None
    nonce = None
    if payload.api_key:
        ciphertext, nonce = SecretCipher(get_settings().secret_key_base64).encrypt(
            payload.api_key,
            authenticated_data=f"{payload.provider}:{payload.model_id}",
        )
    configuration = ModelConfiguration(
        name=payload.name,
        provider=payload.provider,
        model_id=payload.model_id,
        base_url=payload.base_url,
        billing_currency=payload.billing_currency,
        provider_options=payload.provider_options,
        capabilities=sorted(capability.value for capability in payload.capabilities),
        encrypted_api_key=ciphertext,
        api_key_nonce=nonce,
        key_suffix=payload.api_key[-4:] if payload.api_key else None,
        created_by_user_id=user.id,
    )
    session.add(configuration)
    await session.flush()
    await record_audit_event(
        session,
        event_type="model.created",
        actor_user_id=user.id,
        details={
            "model_configuration_id": str(configuration.id),
            "provider": configuration.provider,
            "model_id": configuration.model_id,
            "has_key": ciphertext is not None,
        },
    )
    await session.commit()
    await session.refresh(configuration)
    return configuration


async def update_model_configuration(
    session: AsyncSession,
    *,
    configuration: ModelConfiguration,
    payload: ModelUpdate,
    user: User,
) -> ModelConfiguration:
    changes = payload.model_dump(exclude_unset=True)
    old_provider = configuration.provider
    old_model_id = configuration.model_id
    cipher = SecretCipher(get_settings().secret_key_base64)
    existing_secret: str | None = None
    if configuration.encrypted_api_key is not None and configuration.api_key_nonce is not None:
        existing_secret = cipher.decrypt(
            configuration.encrypted_api_key,
            configuration.api_key_nonce,
            authenticated_data=f"{old_provider}:{old_model_id}",
        )

    for field in (
        "name",
        "provider",
        "model_id",
        "base_url",
        "billing_currency",
        "provider_options",
        "is_enabled",
    ):
        if field in changes:
            setattr(configuration, field, changes[field])
    if payload.capabilities is not None:
        configuration.capabilities = sorted(value.value for value in payload.capabilities)

    secret = payload.api_key if payload.api_key else existing_secret
    if payload.clear_api_key:
        secret = None
    if secret is None:
        configuration.encrypted_api_key = None
        configuration.api_key_nonce = None
        configuration.key_suffix = None
    elif payload.api_key or configuration.provider != old_provider or configuration.model_id != old_model_id:
        ciphertext, nonce = cipher.encrypt(
            secret,
            authenticated_data=f"{configuration.provider}:{configuration.model_id}",
        )
        configuration.encrypted_api_key = ciphertext
        configuration.api_key_nonce = nonce
        configuration.key_suffix = secret[-4:]

    await record_audit_event(
        session,
        event_type="model.updated",
        actor_user_id=user.id,
        details={
            "model_configuration_id": str(configuration.id),
            "fields": sorted(key for key in changes if key != "api_key"),
            "key_rotated": bool(payload.api_key),
            "key_cleared": payload.clear_api_key,
            "is_enabled": configuration.is_enabled,
        },
    )
    await session.commit()
    await session.refresh(configuration)
    return configuration
