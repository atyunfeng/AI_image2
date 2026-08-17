from io import BytesIO

import pytest
from PIL import Image

from aiimage.composition.text import CompositionError, TextLayer, render_text_layers


def _source(width: int = 200, height: int = 100) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_text_compositor_preserves_canvas_and_is_deterministic() -> None:
    layer = TextLayer("Material", (100, 10, 190, 90), 16, "#111111")
    first, mime_type = render_text_layers(_source(), [layer])
    second, _ = render_text_layers(_source(), [layer])
    assert first == second
    assert mime_type == "image/png"
    assert Image.open(BytesIO(first)).size == (200, 100)


def test_text_compositor_converts_to_jpeg() -> None:
    content, mime_type = render_text_layers(_source(), [], output_format="JPEG")
    assert mime_type == "image/jpeg"
    assert Image.open(BytesIO(content)).format == "JPEG"


def test_text_region_must_stay_inside_canvas() -> None:
    with pytest.raises(CompositionError, match="outside"):
        render_text_layers(_source(), [TextLayer("copy", (0, 0, 201, 90), 16, "black")])
