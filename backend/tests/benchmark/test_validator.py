from pathlib import Path

import pytest

from aiimage.benchmark.validator import BenchmarkValidationError, validate_manifest


def _manifest(path: Path):
    products = []
    for category in ("apparel", "shoes", "hats"):
        for index in range(10):
            name = f"{category}-{index}.png"
            (path / name).write_bytes(b"image")
            products.append(
                {
                    "sku": f"{category}-{index}",
                    "category": category,
                    "references": [{"view": "front", "path": name}],
                    "truth_anchors": {},
                    "requested_views": ["front"],
                }
            )
    return {"version": 1, "products": products}


def test_manifest_requires_ten_per_category(tmp_path: Path):
    data = _manifest(tmp_path)
    data["products"].pop()
    with pytest.raises(BenchmarkValidationError, match="hats requires 10 products; found 9"):
        validate_manifest(data, base_dir=tmp_path)


def test_valid_thirty_sku_manifest(tmp_path: Path):
    assert len(validate_manifest(_manifest(tmp_path), base_dir=tmp_path).products) == 30
