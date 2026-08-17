from io import BytesIO

from PIL import Image

from aiimage.editing.images import compose_image, process_mask


def test_mask_processing_resizes_inverts_dilates_and_feathers() -> None:
    source = Image.new("L", (8, 8), 0)
    source.putpixel((4, 4), 255)
    buffer = BytesIO()
    source.save(buffer, format="PNG")
    processed = process_mask(
        buffer.getvalue(), width=16, height=16, invert=False, dilation=2, feather=1
    )
    with Image.open(BytesIO(processed)) as mask:
        assert mask.size == (16, 16)
        assert mask.mode == "L"
        assert mask.getbbox() is not None


def test_deterministic_composition_changes_canvas_and_adds_text(png_bytes) -> None:
    output, mime_type = compose_image(
        png_bytes,
        parameters={
            "canvas_width": 96,
            "canvas_height": 80,
            "scale": 2,
            "rotation": 5,
            "x": 10,
            "y": 12,
            "text_layers": [
                {
                    "text": "新品",
                    "region": [4, 4, 92, 40],
                    "font_size": 12,
                    "color": "#111111",
                }
            ],
        },
    )
    with Image.open(BytesIO(output)) as image:
        assert image.size == (96, 80)
        assert image.format == "PNG"
    assert mime_type == "image/png"
