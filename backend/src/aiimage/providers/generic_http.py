import base64
import hashlib

import httpx

from aiimage.models.domain import GenerationRequest, GenerationResult


class GenericHttpProvider:
    def __init__(self, *, base_url: str, api_key: str, model_id: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_id = model_id

    async def test_connection(self) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/health",
                headers=self._headers(),
            )
        response.raise_for_status()

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        payload = {
            "model": self.model_id,
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height,
            "reference_images": [
                {
                    "mime_type": image.mime_type,
                    "base64": base64.b64encode(image.content).decode(),
                }
                for image in request.reference_images
            ],
            "parameters": request.parameters,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/generate",
                headers=self._headers(),
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
        content = base64.b64decode(data["image_base64"], validate=True)
        if len(content) > 25 * 1024 * 1024:
            raise ValueError("Provider image exceeds 25 MiB")
        return GenerationResult(
            content=content,
            mime_type=data.get("mime_type", "image/png"),
            content_sha256=hashlib.sha256(content).hexdigest(),
            provider_request_id=data["request_id"],
            estimated_cost_minor=int(data.get("cost_minor", 0)),
        )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

