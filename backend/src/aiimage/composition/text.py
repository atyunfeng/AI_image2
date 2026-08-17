from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


class CompositionError(ValueError):
    pass


@dataclass(frozen=True)
class TextLayer:
    text: str
    region: tuple[int, int, int, int]
    font_size: int
    color: str
    align: str = "left"


_FONT_CANDIDATES = (
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default(size=size)


def _wrapped_lines(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        current = ""
        for character in paragraph:
            candidate = current + character
            width = draw.textbbox((0, 0), candidate, font=font)[2]
            if current and width > max_width:
                lines.append(current)
                current = character
            else:
                current = candidate
        lines.append(current)
    return lines


def render_text_layers(
    source: bytes,
    layers: list[TextLayer],
    *,
    output_format: str = "PNG",
) -> tuple[bytes, str]:
    with Image.open(BytesIO(source)) as opened:
        image = opened.convert("RGBA")
    draw = ImageDraw.Draw(image)
    for layer in layers:
        left, top, right, bottom = layer.region
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            raise CompositionError("Text region is outside the canvas")
        if layer.font_size < 8:
            raise CompositionError("Font size is below the rendering minimum")
        font = _font(layer.font_size)
        lines = _wrapped_lines(draw, layer.text, font, right - left)
        line_height = max(layer.font_size, draw.textbbox((0, 0), "Ag", font=font)[3])
        if len(lines) * line_height > bottom - top:
            raise CompositionError("Authoritative copy does not fit the declared text region")
        y = top
        for line in lines:
            line_width = draw.textbbox((0, 0), line, font=font)[2]
            x = left if layer.align == "left" else right - line_width
            draw.text((x, y), line, font=font, fill=layer.color)
            y += line_height

    normalized_format = output_format.upper()
    if normalized_format not in {"PNG", "JPEG", "WEBP"}:
        raise CompositionError("Unsupported output format")
    buffer = BytesIO()
    if normalized_format == "JPEG":
        flattened = Image.new("RGB", image.size, "white")
        flattened.paste(image, mask=image.getchannel("A"))
        flattened.save(buffer, format="JPEG", quality=95, optimize=False)
        mime_type = "image/jpeg"
    else:
        image.save(buffer, format=normalized_format, optimize=False)
        mime_type = {"PNG": "image/png", "WEBP": "image/webp"}[normalized_format]
    return buffer.getvalue(), mime_type
