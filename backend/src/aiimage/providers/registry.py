from aiimage.models.domain import ProviderAdapter
from aiimage.models.models import ModelConfiguration
from aiimage.models.secrets import SecretCipher
from aiimage.providers.comfyui import ComfyUIProvider
from aiimage.providers.generic_http import GenericHttpProvider
from aiimage.providers.mock import MockProvider


class ProviderRegistry:
    def __init__(self, *, secret_key_base64: str, allow_private_urls: bool = False) -> None:
        self.cipher = SecretCipher(secret_key_base64)
        self.allow_private_urls = allow_private_urls

    def _validate_base_url(self, base_url: str) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
            raise ValueError("Provider base URL must be an HTTP(S) origin without credentials")
        if self.allow_private_urls:
            return
        if parsed.hostname.lower() == "localhost":
            raise ValueError("Private Provider URLs are disabled")
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError:
            return
        if not address.is_global:
            raise ValueError("Private Provider URLs are disabled")

    def get(self, configuration: ModelConfiguration) -> ProviderAdapter:
        if configuration.provider == "mock":
            return MockProvider()
        if configuration.provider == "generic_http":
            if not configuration.base_url:
                raise ValueError("Generic HTTP provider requires a base URL")
            self._validate_base_url(configuration.base_url)
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
        if configuration.provider == "comfyui":
            if not configuration.base_url:
                raise ValueError("ComfyUI provider requires a base URL")
            self._validate_base_url(configuration.base_url)
            api_key = None
            if configuration.encrypted_api_key is not None and configuration.api_key_nonce is not None:
                api_key = self.cipher.decrypt(
                    configuration.encrypted_api_key,
                    configuration.api_key_nonce,
                    authenticated_data=f"{configuration.provider}:{configuration.model_id}",
                )
            options = configuration.provider_options or {}
            return ComfyUIProvider(
                base_url=configuration.base_url,
                api_key=api_key,
                workflow=options.get("workflow", {}),
                bindings=options.get("bindings", {}),
                reference_bindings=options.get("reference_bindings", []),
                output_node_id=options.get("output_node_id"),
                timeout_seconds=int(options.get("timeout_seconds", 180)),
                cost_minor=int(options.get("cost_minor", 0)),
            )
        raise ValueError(f"Unsupported provider: {configuration.provider}")
import ipaddress
from urllib.parse import urlparse
