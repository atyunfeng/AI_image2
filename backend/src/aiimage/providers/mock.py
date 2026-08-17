import hashlib
import json
from io import BytesIO

from PIL import Image, ImageDraw

from aiimage.models.domain import GenerationRequest, GenerationResult


class MockProvider:
    async def test_connection(self) -> None:
        return None

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        serializable = request.model_dump(exclude={"reference_images"})
        serializable["reference_images"] = [
            {
                "mime_type": reference.mime_type,
                "sha256": hashlib.sha256(reference.content).hexdigest(),
            }
            for reference in request.reference_images
        ]
        request_hash = hashlib.sha256(
            json.dumps(serializable, sort_keys=True).encode()
        ).hexdigest()
        white_background = request.parameters.get("background") == "white"
        background = "white" if white_background else f"#{request_hash[:6]}"
        image = Image.new("RGB", (request.width, request.height), color=background)
        draw = ImageDraw.Draw(image)
        inset = max(16, min(request.width, request.height) // 5)
        draw.rounded_rectangle(
            (inset, inset, request.width - inset, request.height - inset),
            radius=max(4, inset // 8),
            fill=f"#{request_hash[6:12]}",
        )
        draw.text((inset + 8, inset + 8), request_hash[:16], fill="white")
        buffer = BytesIO()
        image.save(buffer, format="PNG", optimize=False)
        content = buffer.getvalue()
        digest = hashlib.sha256(content).hexdigest()
        return GenerationResult(
            content=content,
            mime_type="image/png",
            content_sha256=digest,
            provider_request_id=f"mock-{request_hash[:24]}",
            estimated_cost_minor=0,
        )
