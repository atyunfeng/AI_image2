from copy import deepcopy
from typing import Any

_PLATFORM_PACKS: tuple[dict[str, Any], ...] = (
    {
        "slug": "taobao-tmall-cn",
        "name": "淘宝 / 天猫（中国站）",
        "kind": "platform",
        "rules": {
            "market": "CN",
            "locale": "zh-CN",
            "format": "PNG",
            "max_file_bytes": 5_242_880,
            "safe_margin": 0.05,
            "slots": [
                {
                    "key": "hero_front",
                    "label": "正面主图",
                    "view": "front",
                    "width": 2000,
                    "height": 2000,
                    "background": "white",
                    "allow_text": False,
                },
                {
                    "key": "detail_material",
                    "label": "材质详情",
                    "view": "detail",
                    "width": 1464,
                    "height": 600,
                    "background": "brand",
                    "allow_text": True,
                    "text_region": [732, 48, 1404, 552],
                },
                {
                    "key": "detail_feature",
                    "label": "卖点详情",
                    "view": "front",
                    "width": 1464,
                    "height": 600,
                    "background": "brand",
                    "allow_text": True,
                    "text_region": [732, 48, 1404, 552],
                },
            ],
        },
    },
    {
        "slug": "amazon-global",
        "name": "Amazon（全球默认）",
        "kind": "platform",
        "rules": {
            "market": "GLOBAL",
            "locale": "en-US",
            "format": "JPEG",
            "max_file_bytes": 10_485_760,
            "safe_margin": 0.05,
            "slots": [
                {
                    "key": "hero_front",
                    "label": "正面主图",
                    "view": "front",
                    "width": 2000,
                    "height": 2000,
                    "background": "white",
                    "allow_text": False,
                },
                {
                    "key": "detail_material",
                    "label": "材质详情",
                    "view": "detail",
                    "width": 2000,
                    "height": 2000,
                    "background": "brand",
                    "allow_text": True,
                    "text_region": [1040, 120, 1880, 1880],
                },
                {
                    "key": "detail_feature",
                    "label": "卖点详情",
                    "view": "front",
                    "width": 2000,
                    "height": 2000,
                    "background": "brand",
                    "allow_text": True,
                    "text_region": [1040, 120, 1880, 1880],
                },
            ],
        },
    },
    {
        "slug": "tiktok-shop-global",
        "name": "TikTok Shop（全球默认）",
        "kind": "platform",
        "rules": {
            "market": "GLOBAL",
            "locale": "en-US",
            "format": "JPEG",
            "max_file_bytes": 5_242_880,
            "safe_margin": 0.06,
            "slots": [
                {
                    "key": "hero_front",
                    "label": "正面主图",
                    "view": "front",
                    "width": 1200,
                    "height": 1200,
                    "background": "white",
                    "allow_text": False,
                },
                {
                    "key": "detail_material",
                    "label": "材质详情",
                    "view": "detail",
                    "width": 1200,
                    "height": 1500,
                    "background": "brand",
                    "allow_text": True,
                    "text_region": [624, 90, 1128, 1410],
                },
                {
                    "key": "detail_feature",
                    "label": "卖点详情",
                    "view": "front",
                    "width": 1200,
                    "height": 1500,
                    "background": "brand",
                    "allow_text": True,
                    "text_region": [624, 90, 1128, 1410],
                },
            ],
        },
    },
)

_SUPPORT_PACKS: tuple[dict[str, Any], ...] = (
    {
        "slug": "apparel-core",
        "name": "服装基础套图",
        "kind": "category",
        "rules": {
            "category": "apparel",
            "slots": {
                "hero_front": {"required_reference_views": ["front"]},
                "detail_material": {"required_reference_views": ["detail"]},
                "detail_feature": {"required_reference_views": ["front"]},
            },
        },
    },
    {
        "slug": "brand-neutral",
        "name": "默认中性品牌视觉",
        "kind": "brand",
        "rules": {
            "palette": {"background": "#F4F1EA", "text": "#16181D"},
            "font": "system-sans",
            "minimum_font_size": 24,
            "copy": {"detail_material": "材质细节", "detail_feature": "设计亮点"},
        },
    },
)


def first_party_platform_packs() -> list[dict[str, Any]]:
    return deepcopy(list(_PLATFORM_PACKS))


def first_party_packs() -> list[dict[str, Any]]:
    return deepcopy([*_PLATFORM_PACKS, *_SUPPORT_PACKS])
