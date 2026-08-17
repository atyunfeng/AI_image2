import hashlib

import pytest

from aiimage.models.domain import Capability, GenerationRequest, ReferenceImage
from aiimage.providers.comfyui import ComfyUIProvider


class FakeResponse:
    def __init__(self, *, data=None, content=b"", content_type="application/json") -> None:
        self._data = data or {}
        self.content = content
        self.headers = {"content-type": content_type}

    def json(self):
        return self._data

    def raise_for_status(self) -> None:
        return None


class FakeClient:
    submitted_workflow = None

    def __init__(self, **kwargs) -> None:
        del kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args) -> None:
        return None

    async def post(self, url, **kwargs):
        if url.endswith("/upload/image"):
            return FakeResponse(data={"name": "uploaded.png"})
        if url.endswith("/prompt"):
            FakeClient.submitted_workflow = kwargs["json"]["prompt"]
            return FakeResponse(data={"prompt_id": "comfy-123"})
        raise AssertionError(url)

    async def get(self, url, **kwargs):
        del kwargs
        if "/history/" in url:
            return FakeResponse(
                data={
                    "comfy-123": {
                        "outputs": {
                            "9": {
                                "images": [
                                    {"filename": "result.png", "subfolder": "", "type": "output"}
                                ]
                            }
                        }
                    }
                }
            )
        if url.endswith("/view"):
            return FakeResponse(content=PNG_1X1, content_type="image/png")
        return FakeResponse(data={"system": {"os": "posix"}})


PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xcf\xc0\x00\x00"
    b"\x03\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.mark.asyncio
async def test_comfyui_uploads_reference_binds_workflow_and_downloads(monkeypatch) -> None:
    monkeypatch.setattr("aiimage.providers.comfyui.httpx.AsyncClient", FakeClient)
    provider = ComfyUIProvider(
        base_url="http://comfy.local",
        api_key=None,
        workflow={
            "6": {"inputs": {"text": ""}},
            "7": {"inputs": {"width": 512, "height": 512}},
            "12": {"inputs": {"image": ""}},
        },
        bindings={
            "prompt": ["6", "inputs", "text"],
            "width": ["7", "inputs", "width"],
            "height": ["7", "inputs", "height"],
        },
        reference_bindings=[["12", "inputs", "image"]],
        output_node_id="9",
        cost_minor=9,
    )
    await provider.test_connection()
    result = await provider.generate(
        GenerationRequest(
            idempotency_key="comfy-test",
            capability=Capability.REFERENCE_TO_IMAGE,
            prompt="商品白底主图",
            reference_images=[ReferenceImage(content=PNG_1X1, mime_type="image/png")],
            width=1024,
            height=1200,
            parameters={},
        )
    )

    assert FakeClient.submitted_workflow["6"]["inputs"]["text"] == "商品白底主图"
    assert FakeClient.submitted_workflow["7"]["inputs"] == {"width": 1024, "height": 1200}
    assert FakeClient.submitted_workflow["12"]["inputs"]["image"] == "uploaded.png"
    assert result.provider_request_id == "comfy-123"
    assert result.estimated_cost_minor == 9
    assert result.content_sha256 == hashlib.sha256(PNG_1X1).hexdigest()

