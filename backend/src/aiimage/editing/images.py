from io import BytesIO
from typing import Any

from PIL import Image, ImageFilter

from aiimage.composition.text import TextLayer, render_text_layers


class EditImageError(ValueError):
    pass


def process_mask(
    content: bytes,
    *,
    width: int,
    height: int,
    invert: bool,
    dilation: int,
    feather: float,
) -> bytes:
    if not 0 <= dilation <= 32 or not 0 <= feather <= 32:
        raise EditImageError("Mask dilation and feather must be between 0 and 32")
    try:
        with Image.open(BytesIO(content)) as opened:
            mask = opened.convert("L").resize((width, height), Image.Resampling.LANCZOS)
    except Exception as error:
        raise EditImageError("Mask is not a decodable image") from error
    mask = mask.point(lambda value: 255 if value >= 128 else 0)
    if invert:
        mask = mask.point(lambda value: 255 - value)
    if dilation:
        size = dilation * 2 + 1
        mask = mask.filter(ImageFilter.MaxFilter(size))
    if feather:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))
    output = BytesIO()
    mask.save(output, format="PNG", optimize=False)
    return output.getvalue()


def select_by_corner_color(
    source: bytes, *, foreground: bool, threshold: int = 42
) -> tuple[bytes, int, int]:
    try:
        with Image.open(BytesIO(source)) as opened:
            image = opened.convert("RGB")
    except Exception as error:
        raise EditImageError("Source is not a decodable image") from error
    samples = [
        image.getpixel((0, 0)),
        image.getpixel((image.width - 1, 0)),
        image.getpixel((0, image.height - 1)),
        image.getpixel((image.width - 1, image.height - 1)),
    ]
    background = tuple(round(sum(sample[index] for sample in samples) / 4) for index in range(3))
    mask = Image.new("L", image.size)
    pixels = []
    for pixel in image.getdata():
        distance = sum((pixel[index] - background[index]) ** 2 for index in range(3)) ** 0.5
        selected = distance >= threshold if foreground else distance < threshold
        pixels.append(255 if selected else 0)
    mask.putdata(pixels)
    buffer = BytesIO()
    mask.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue(), image.width, image.height


def compose_image(
    source: bytes,
    *,
    parameters: dict[str, Any],
    logo: bytes | None = None,
    image_layers: list[tuple[bytes, dict[str, Any]]] | None = None,
) -> tuple[bytes, str]:
    try:
        with Image.open(BytesIO(source)) as opened:
            original = opened.convert("RGBA")
    except Exception as error:
        raise EditImageError("Source is not a decodable image") from error
    canvas_width = int(parameters.get("canvas_width", original.width))
    canvas_height = int(parameters.get("canvas_height", original.height))
    if not 64 <= canvas_width <= 4096 or not 64 <= canvas_height <= 4096:
        raise EditImageError("Canvas dimensions must be between 64 and 4096")
    crop = parameters.get("crop")
    foreground = original
    if crop:
        box = tuple(int(value) for value in crop)
        if len(box) != 4 or not (0 <= box[0] < box[2] <= original.width and 0 <= box[1] < box[3] <= original.height):
            raise EditImageError("Crop is outside the source image")
        foreground = original.crop(box)
    scale = float(parameters.get("scale", 1))
    if not 0.1 <= scale <= 4:
        raise EditImageError("Scale must be between 0.1 and 4")
    foreground = foreground.resize(
        (max(1, round(foreground.width * scale)), max(1, round(foreground.height * scale))),
        Image.Resampling.LANCZOS,
    )
    rotation = float(parameters.get("rotation", 0))
    foreground = foreground.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
    if parameters.get("background_blur", 0):
        background = original.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
        background = background.filter(
            ImageFilter.GaussianBlur(radius=float(parameters["background_blur"]))
        )
    else:
        background = Image.new(
            "RGBA", (canvas_width, canvas_height), parameters.get("background_color", "#ffffff")
        )
    x = int(parameters.get("x", (canvas_width - foreground.width) // 2))
    y = int(parameters.get("y", (canvas_height - foreground.height) // 2))
    background.alpha_composite(foreground, (x, y))
    if logo:
        with Image.open(BytesIO(logo)) as opened_logo:
            logo_image = opened_logo.convert("RGBA")
        logo_width = int(parameters.get("logo_width", min(logo_image.width, canvas_width // 4)))
        logo_height = max(1, round(logo_image.height * logo_width / logo_image.width))
        logo_image = logo_image.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        opacity = max(0.0, min(1.0, float(parameters.get("logo_opacity", 1))))
        logo_image.putalpha(logo_image.getchannel("A").point(lambda value: round(value * opacity)))
        background.alpha_composite(
            logo_image,
            (int(parameters.get("logo_x", 24)), int(parameters.get("logo_y", 24))),
        )
    for layer_content, layer in image_layers or []:
        with Image.open(BytesIO(layer_content)) as opened_layer:
            layer_image = opened_layer.convert("RGBA")
        width = int(layer.get("width", layer_image.width))
        height = max(1, round(layer_image.height * width / layer_image.width))
        layer_image = layer_image.resize((width, height), Image.Resampling.LANCZOS)
        opacity = max(0.0, min(1.0, float(layer.get("opacity", 1))))
        layer_image.putalpha(
            layer_image.getchannel("A").point(
                lambda value, layer_opacity=opacity: round(value * layer_opacity)
            )
        )
        background.alpha_composite(
            layer_image,
            (int(layer.get("x", 0)), int(layer.get("y", 0))),
        )
    buffer = BytesIO()
    background.save(buffer, format="PNG", optimize=False)
    result = buffer.getvalue()
    layers = [
        TextLayer(
            text=str(layer["text"]),
            region=tuple(int(value) for value in layer["region"]),
            font_size=int(layer.get("font_size", 40)),
            color=str(layer.get("color", "#16181D")),
            align=str(layer.get("align", "left")),
        )
        for layer in parameters.get("text_layers", [])
        if str(layer.get("text", "")).strip()
    ]
    return render_text_layers(result, layers, output_format="PNG")
