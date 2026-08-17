from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.auth.models import User
from aiimage.config import get_settings
from aiimage.models.models import ModelConfiguration
from aiimage.models.schemas import ModelCreate, ModelResponse
from aiimage.models.secrets import SecretCipher


def to_response(configuration: ModelConfiguration) -> ModelResponse:
    return ModelResponse(
        id=configuration.id,
        name=configuration.name,
        provider=configuration.provider,
        model_id=configuration.model_id,
        base_url=configuration.base_url,
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
        capabilities=sorted(capability.value for capability in payload.capabilities),
        encrypted_api_key=ciphertext,
        api_key_nonce=nonce,
        key_suffix=payload.api_key[-4:] if payload.api_key else None,
        created_by_user_id=user.id,
    )
    session.add(configuration)
    await session.commit()
    await session.refresh(configuration)
    return configuration

