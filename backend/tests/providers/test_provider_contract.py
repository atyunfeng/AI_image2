from aiimage.models.domain import Capability, GenerationRequest
from aiimage.providers.mock import MockProvider


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

