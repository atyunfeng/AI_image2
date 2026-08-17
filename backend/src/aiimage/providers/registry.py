from aiimage.models.domain import ProviderAdapter
from aiimage.models.models import ModelConfiguration
from aiimage.models.secrets import SecretCipher
from aiimage.providers.generic_http import GenericHttpProvider
from aiimage.providers.mock import MockProvider


class ProviderRegistry:
    def __init__(self, *, secret_key_base64: str) -> None:
        self.cipher = SecretCipher(secret_key_base64)

    def get(self, configuration: ModelConfiguration) -> ProviderAdapter:
        if configuration.provider == "mock":
            return MockProvider()
        if configuration.provider == "generic_http":
            if not configuration.base_url:
                raise ValueError("Generic HTTP provider requires a base URL")
            if configuration.encrypted_api_key is None or configuration.api_key_nonce is None:
                raise ValueError("Generic HTTP provider requires an API key")
            api_key = self.cipher.decrypt(
                configuration.encrypted_api_key,
                configuration.api_key_nonce,
                authenticated_data=f"{configuration.provider}:{configuration.model_id}",
            )
            return GenericHttpProvider(
                base_url=configuration.base_url,
                api_key=api_key,
                model_id=configuration.model_id,
            )
        raise ValueError(f"Unsupported provider: {configuration.provider}")

