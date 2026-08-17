import asyncio
import copy
import hashlib
from typing import Any
from uuid import uuid4

import httpx

from aiimage.models.domain import GenerationRequest, GenerationResult


class ComfyUIProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        workflow: dict[str, Any],
        bindings: dict[str, list[str]],
        reference_bindings: list[list[str]],
        output_node_id: str | None,
        timeout_seconds: int = 180,
        cost_minor: int = 0,
    ) -> None:
        if not workflow:
            raise ValueError("ComfyUI provider requires provider_options.workflow")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.workflow = workflow
        self.bindings = bindings
        self.reference_bindings = reference_bindings
        self.output_node_id = output_node_id
        self.timeout_seconds = timeout_seconds
        self.cost_minor = cost_minor

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    async def test_connection(self) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.base_url}/system_stats", headers=self._headers())
        response.raise_for_status()

    @staticmethod
    def _set_path(document: dict[str, Any], path: list[str], value: Any) -> None:
        if not path:
            raise ValueError("ComfyUI binding path cannot be empty")
        target: Any = document
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        workflow = copy.deepcopy(self.workflow)
        for key, value in {
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height,
        }.items():
            if path := self.bindings.get(key):
                self._set_path(workflow, path, value)

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for index, image in enumerate(request.reference_images):
                if index >= len(self.reference_bindings):
                    break
                filename = f"aiimage-{request.idempotency_key[:16]}-{index}.png"
                upload = await client.post(
                    f"{self.base_url}/upload/image",
                    headers=self._headers(),
                    files={"image": (filename, image.content, image.mime_type)},
                    data={"overwrite": "true", "type": "input"},
                )
                upload.raise_for_status()
                uploaded = upload.json()
                self._set_path(workflow, self.reference_bindings[index], uploaded["name"])

            queued = await client.post(
                f"{self.base_url}/prompt",
                headers=self._headers(),
                json={
                    "prompt": workflow,
                    "client_id": str(uuid4()),
                    "extra_data": {"aiimage_idempotency_key": request.idempotency_key},
                },
            )
            queued.raise_for_status()
            prompt_id = str(queued.json()["prompt_id"])
            history_item: dict[str, Any] | None = None
            for _ in range(max(1, self.timeout_seconds * 2)):
                history = await client.get(
                    f"{self.base_url}/history/{prompt_id}", headers=self._headers()
                )
                history.raise_for_status()
                history_item = history.json().get(prompt_id)
                if history_item:
                    break
                await asyncio.sleep(0.5)
            if history_item is None:
                raise TimeoutError("ComfyUI generation timed out")
            outputs = history_item.get("outputs", {})
            selected = outputs.get(self.output_node_id) if self.output_node_id else None
            if selected is None:
                selected = next(
                    (value for value in outputs.values() if value.get("images")), None
                )
            if not selected or not selected.get("images"):
                raise ValueError("ComfyUI history contains no output image")
            image = selected["images"][0]
            downloaded = await client.get(
                f"{self.base_url}/view",
                headers=self._headers(),
                params={
                    "filename": image["filename"],
                    "subfolder": image.get("subfolder", ""),
                    "type": image.get("type", "output"),
                },
            )
            downloaded.raise_for_status()
        content_type = downloaded.headers.get("content-type", "image/png").split(";")[0]
        if content_type not in {"image/png", "image/jpeg", "image/webp"}:
            raise ValueError("ComfyUI returned an unsupported image type")
        return GenerationResult(
            content=downloaded.content,
            mime_type=content_type,
            content_sha256=hashlib.sha256(downloaded.content).hexdigest(),
            provider_request_id=prompt_id,
            estimated_cost_minor=self.cost_minor,
        )

