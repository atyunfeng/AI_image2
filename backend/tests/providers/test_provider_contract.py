import pytest

from aiimage.config import get_settings
from aiimage.models.domain import Capability, GenerationRequest
from aiimage.providers.mock import MockProvider
from aiimage.providers.registry import ProviderRegistry


async def test_mock_provider_is_deterministic() -> None:
    provider = MockProvider()
    request = GenerationRequest(
        idempotency_key="stable-request",
        capability=Capability.REFERENCE_TO_IMAGE,
        prompt="White background product image",
        reference_images=[],
        width=256,
        height=256,
        parameters={},
    )

    first = await provider.generate(request)
    second = await provider.generate(request)

    assert first.content_sha256 == second.content_sha256
    assert first.content == second.content


def test_provider_registry_blocks_private_urls_by_default() -> None:
    registry = ProviderRegistry(secret_key_base64=get_settings().secret_key_base64)
    with pytest.raises(ValueError, match="Private Provider URLs"):
        registry._validate_base_url("http://127.0.0.1:8188")

    allowed = ProviderRegistry(
        secret_key_base64=get_settings().secret_key_base64,
        allow_private_urls=True,
    )
    allowed._validate_base_url("http://127.0.0.1:8188")
