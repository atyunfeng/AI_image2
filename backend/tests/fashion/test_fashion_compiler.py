import pytest

from aiimage.fashion.compiler import FashionCompilationError, compile_fashion_plan
from aiimage.fashion.schemas import FashionOutput
from aiimage.models.domain import Capability


def test_compiler_routes_tryon_and_multi_angle_capabilities() -> None:
    slots = compile_fashion_plan(
        category="apparel",
        requested_outputs=[FashionOutput.MODEL_SIDE, FashionOutput.VIRTUAL_TRY_ON],
        product_views={"front", "side"},
        model_views={"front", "side"},
        mode="strict",
    )
    assert [slot.capability for slot in slots] == [
        Capability.MULTI_REFERENCE_TO_IMAGE,
        Capability.VIRTUAL_TRY_ON,
    ]
    assert all(not slot.inferred_view for slot in slots)


def test_strict_mode_rejects_missing_product_angle() -> None:
    with pytest.raises(FashionCompilationError, match="side"):
        compile_fashion_plan(
            category="shoes",
            requested_outputs=[FashionOutput.MODEL_SIDE],
            product_views={"front"},
            model_views={"side"},
            mode="strict",
        )


def test_creative_mode_labels_inferred_product_angle() -> None:
    slot = compile_fashion_plan(
        category="hats",
        requested_outputs=[FashionOutput.MODEL_BACK],
        product_views={"front"},
        model_views={"back"},
        mode="creative",
    )[0]
    assert slot.inferred_view
