from dataclasses import dataclass

from aiimage.fashion.schemas import FashionOutput
from aiimage.models.domain import Capability


class FashionCompilationError(ValueError):
    pass


@dataclass(frozen=True)
class FashionSlot:
    output: FashionOutput
    capability: Capability
    requested_view: str
    required_product_views: frozenset[str]
    required_model_views: frozenset[str]
    label: str
    prompt: str
    inferred_view: bool


_OUTPUT_RULES = {
    FashionOutput.PRODUCT_FRONT: (
        Capability.REFERENCE_TO_IMAGE,
        "front",
        {"front"},
        set(),
        "商品正面图",
    ),
    FashionOutput.MODEL_FRONT: (
        Capability.MULTI_REFERENCE_TO_IMAGE,
        "front",
        {"front"},
        {"front", "full_body"},
        "模特正面图",
    ),
    FashionOutput.MODEL_SIDE: (
        Capability.MULTI_REFERENCE_TO_IMAGE,
        "side",
        {"side"},
        {"side", "full_body"},
        "模特侧面图",
    ),
    FashionOutput.MODEL_BACK: (
        Capability.MULTI_REFERENCE_TO_IMAGE,
        "back",
        {"back"},
        {"back", "full_body"},
        "模特背面图",
    ),
    FashionOutput.DETAIL: (
        Capability.REFERENCE_TO_IMAGE,
        "detail",
        {"detail", "front"},
        set(),
        "商品细节图",
    ),
    FashionOutput.VIRTUAL_TRY_ON: (
        Capability.VIRTUAL_TRY_ON,
        "front",
        {"front"},
        {"front", "full_body"},
        "虚拟试穿图",
    ),
}


def compile_fashion_plan(
    *,
    category: str,
    requested_outputs: list[FashionOutput],
    product_views: set[str],
    model_views: set[str],
    mode: str,
) -> tuple[FashionSlot, ...]:
    if category not in {"apparel", "shoes", "hats"}:
        raise FashionCompilationError("Fashion workflows support apparel, shoes, and hats")
    if len(set(requested_outputs)) != len(requested_outputs):
        raise FashionCompilationError("Fashion outputs must be unique")
    slots: list[FashionSlot] = []
    for output in requested_outputs:
        capability, view, product_required, model_required, label = _OUTPUT_RULES[output]
        missing_product = bool(product_required) and not product_required.intersection(product_views)
        missing_model = bool(model_required) and not model_required.intersection(model_views)
        if missing_model:
            raise FashionCompilationError(f"{label} requires a matching model reference")
        if mode == "strict" and missing_product:
            choices = "/".join(sorted(product_required))
            raise FashionCompilationError(f"{label} requires product reference: {choices}")
        category_name = {"apparel": "garment", "shoes": "shoes", "hats": "hat"}[category]
        slots.append(
            FashionSlot(
                output=output,
                capability=capability,
                requested_view=view,
                required_product_views=frozenset(product_required),
                required_model_views=frozenset(model_required),
                label=label,
                prompt=(
                    f"Create {label} for {category_name} commerce. Preserve exact product color, "
                    "material, logo, pattern and construction. Preserve the selected model identity."
                ),
                inferred_view=missing_product,
            )
        )
    return tuple(slots)
