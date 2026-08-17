from dataclasses import dataclass
from io import BytesIO
from typing import Any

from PIL import Image


@dataclass(frozen=True)
class CheckResult:
    code: str
    passed: bool
    blocking: bool
    expected: dict[str, Any]
    measured: dict[str, Any]
    message: str


def _result(
    code: str,
    passed: bool,
    expected: dict[str, Any],
    measured: dict[str, Any],
    message: str,
) -> CheckResult:
    return CheckResult(code, passed, True, expected, measured, message)


def inspect_structure(content: bytes, mime_type: str, rules: dict[str, Any]) -> list[CheckResult]:
    with Image.open(BytesIO(content)) as opened:
        image_format = opened.format
        image = opened.convert("RGB")
    expected_format = rules.get("format", "PNG").upper()
    dimensions_match = image.size == (rules["width"], rules["height"])
    size_matches = len(content) <= rules["max_file_bytes"]
    checks = [
        _result(
            "format",
            image_format == expected_format,
            {"format": expected_format},
            {"format": image_format, "mime_type": mime_type},
            "图片格式符合规则" if image_format == expected_format else "图片格式不符合规则",
        ),
        _result(
            "dimensions",
            dimensions_match,
            {"width": rules["width"], "height": rules["height"]},
            {"width": image.width, "height": image.height},
            "图片尺寸符合规则" if dimensions_match else "图片尺寸不符合规则",
        ),
        _result(
            "file_size",
            size_matches,
            {"max_file_bytes": rules["max_file_bytes"]},
            {"size_bytes": len(content)},
            "文件体积符合规则" if size_matches else "文件体积超过规则上限",
        ),
    ]
    text_region = rules.get("text_region")
    if text_region:
        left, top, right, bottom = text_region
        in_bounds = 0 <= left < right <= image.width and 0 <= top < bottom <= image.height
        checks.append(
            _result(
                "text_safe_area",
                in_bounds,
                {"inside_canvas": True},
                {"region": text_region, "inside_canvas": in_bounds},
                "文字安全区在画布内" if in_bounds else "文字安全区超出画布",
            )
        )
    if rules.get("background") == "white":
        inset_x = min(max(1, image.width // 100), image.width - 1)
        inset_y = min(max(1, image.height // 100), image.height - 1)
        samples = [
            image.getpixel((inset_x, inset_y)),
            image.getpixel((image.width - 1 - inset_x, inset_y)),
            image.getpixel((inset_x, image.height - 1 - inset_y)),
            image.getpixel((image.width - 1 - inset_x, image.height - 1 - inset_y)),
        ]
        minimum_channel = min(channel for sample in samples for channel in sample)
        is_white = minimum_channel >= 245
        checks.append(
            _result(
                "white_background_edge",
                is_white,
                {"minimum_corner_channel": 245},
                {"minimum_corner_channel": minimum_channel},
                "画布边缘为白底" if is_white else "画布边缘未达到白底阈值",
            )
        )
    return checks
