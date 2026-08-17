import pytest

from aiimage.templates.compiler import PlanCompilationError, compile_plan
from aiimage.templates.presets import first_party_packs


def _pack(slug: str):
    return next(pack for pack in first_party_packs() if pack["slug"] == slug)


def test_compile_intersects_platform_category_and_brand_rules() -> None:
    platform = _pack("taobao-tmall-cn")
    category = _pack("apparel-core")
    brand = _pack("brand-neutral")
    plan = compile_plan(
        product_category="apparel",
        reference_views={"front"},
        platform_slug=platform["slug"],
        platform_version=1,
        platform_rules=platform["rules"],
        category_slug=category["slug"],
        category_version=1,
        category_rules=category["rules"],
        brand_slug=brand["slug"],
        brand_version=1,
        brand_rules=brand["rules"],
        mode="strict",
    )
    assert [(item.slot, item.width, item.height) for item in plan.items] == [
        ("hero_front", 2000, 2000),
        ("detail_material", 1464, 600),
        ("detail_feature", 1464, 600),
    ]
    assert plan.snapshot["packs"] == {
        "platform": {"slug": "taobao-tmall-cn", "version": 1},
        "category": {"slug": "apparel-core", "version": 1},
        "brand": {"slug": "brand-neutral", "version": 1},
    }
    assert plan.items[0].authoritative_copy is None
    assert plan.items[1].authoritative_copy == "材质细节"


def test_strict_plan_rejects_missing_required_view() -> None:
    platform = _pack("amazon-global")
    category = _pack("apparel-core")
    brand = _pack("brand-neutral")
    with pytest.raises(PlanCompilationError, match="front"):
        compile_plan(
            product_category="apparel",
            reference_views=set(),
            platform_slug=platform["slug"],
            platform_version=1,
            platform_rules=platform["rules"],
            category_slug=category["slug"],
            category_version=1,
            category_rules=category["rules"],
            brand_slug=brand["slug"],
            brand_version=1,
            brand_rules=brand["rules"],
            mode="strict",
        )


def test_compiler_is_deterministic() -> None:
    platform = _pack("tiktok-shop-global")
    category = _pack("apparel-core")
    brand = _pack("brand-neutral")
    kwargs = {
        "product_category": "apparel",
        "reference_views": {"front"},
        "platform_slug": platform["slug"],
        "platform_version": 1,
        "platform_rules": platform["rules"],
        "category_slug": category["slug"],
        "category_version": 1,
        "category_rules": category["rules"],
        "brand_slug": brand["slug"],
        "brand_version": 1,
        "brand_rules": brand["rules"],
        "mode": "strict",
    }
    assert compile_plan(**kwargs).compiler_hash == compile_plan(**kwargs).compiler_hash
