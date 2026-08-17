import hashlib
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from aiimage.benchmark.models import BenchmarkManifest, BenchmarkProduct


class BenchmarkValidationError(RuntimeError):
    pass


def validate_product(product: BenchmarkProduct, *, base_dir: Path) -> None:
    reference_views = {reference.view.value for reference in product.references}
    for requested_view in product.requested_views:
        if requested_view.value in {"side", "back"} and requested_view.value not in reference_views:
            raise BenchmarkValidationError(
                f"{product.sku}: {requested_view.value} reference is required"
            )
    for reference in product.references:
        path = base_dir / reference.path
        if not path.is_file():
            raise BenchmarkValidationError(f"{product.sku}: missing reference {reference.path}")
        if reference.sha256:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != reference.sha256:
                raise BenchmarkValidationError(
                    f"{product.sku}: SHA-256 mismatch for {reference.path}"
                )


def validate_manifest(data: dict[str, Any], *, base_dir: Path) -> BenchmarkManifest:
    try:
        manifest = BenchmarkManifest.model_validate(data)
    except ValidationError as error:
        raise BenchmarkValidationError(str(error)) from error
    counts = Counter(product.category.value for product in manifest.products)
    for category in ("apparel", "shoes", "hats"):
        if counts[category] < 10:
            raise BenchmarkValidationError(
                f"{category} requires 10 products; found {counts[category]}"
            )
    if len({product.sku for product in manifest.products}) != len(manifest.products):
        raise BenchmarkValidationError("Benchmark SKU values must be unique")
    for product in manifest.products:
        validate_product(product, base_dir=base_dir)
    return manifest
