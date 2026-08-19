from aiimage.templates.presets import first_party_packs, first_party_platform_packs


def test_first_party_presets_cover_mainstream_platforms() -> None:
    packs = {pack["slug"]: pack for pack in first_party_platform_packs()}
    assert set(packs) == {
        "taobao-tmall-cn",
        "amazon-global",
        "tiktok-shop-global",
        "jd-cn",
        "pinduoduo-cn",
        "douyin-cn",
        "shopify-global",
        "temu-global",
        "shopee-sea",
        "lazada-sea",
        "ebay-global",
    }
    for slug in set(packs) - {
        "taobao-tmall-cn",
        "amazon-global",
        "tiktok-shop-global",
    }:
        rules = packs[slug]["rules"]
        assert rules["source_note"] == "first_party_default_verify_before_publish"
        assert rules["slots"][0]["key"] == "hero_front"
        assert rules["slots"][0]["allow_text"] is False
    for pack in packs.values():
        governance = pack["rules"]["governance"]
        assert governance["verification_status"] == "requires_official_verification"
        assert governance["official_source_url"] is None


def test_support_presets_include_apparel_and_brand() -> None:
    packs = first_party_packs()
    assert any(pack["slug"] == "apparel-core" for pack in packs)
    assert any(pack["slug"] == "brand-neutral" for pack in packs)
