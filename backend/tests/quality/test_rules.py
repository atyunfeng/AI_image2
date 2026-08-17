from io import BytesIO

from PIL import Image

from aiimage.quality.rules import inspect_structure


def _image(size=(200, 200), color="white", image_format="PNG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format=image_format)
    return buffer.getvalue()


def test_matching_structure_passes() -> None:
    checks = inspect_structure(
        _image(),
        "image/png",
        {
            "width": 200,
            "height": 200,
            "format": "PNG",
            "max_file_bytes": 100_000,
            "background": "white",
        },
    )
    assert all(check.passed for check in checks)


def test_wrong_dimensions_are_blocking() -> None:
    checks = inspect_structure(
        _image((100, 100)),
        "image/png",
        {"width": 200, "height": 200, "format": "PNG", "max_file_bytes": 100_000},
    )
    dimension = next(check for check in checks if check.code == "dimensions")
    assert not dimension.passed
    assert dimension.blocking


def test_non_white_edges_are_blocking_for_white_background() -> None:
    checks = inspect_structure(
        _image(color="#222222"),
        "image/png",
        {
            "width": 200,
            "height": 200,
            "format": "PNG",
            "max_file_bytes": 100_000,
            "background": "white",
        },
    )
    assert not next(check for check in checks if check.code == "white_background_edge").passed
