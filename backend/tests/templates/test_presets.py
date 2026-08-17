from aiimage.templates.presets import first_party_packs, first_party_platform_packs


def test_first_party_presets_cover_initial_platforms() -> None:
    assert {pack["slug"] for pack in first_party_platform_packs()} == {
        "taobao-tmall-cn",
        "amazon-global",
        "tiktok-shop-global",
    }


def test_support_presets_include_apparel_and_brand() -> None:
    packs = first_party_packs()
    assert any(pack["slug"] == "apparel-core" for pack in packs)
    assert any(pack["slug"] == "brand-neutral" for pack in packs)
