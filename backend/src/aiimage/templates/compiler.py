import hashlib
import json
from dataclasses import dataclass
from typing import Any


class PlanCompilationError(ValueError):
    pass


@dataclass(frozen=True)
class CompiledItem:
    position: int
    slot: str
    label: str
    requested_view: str
    width: int
    height: int
    prompt: str
    authoritative_copy: str | None
    rules: dict[str, Any]


@dataclass(frozen=True)
class CompiledPlan:
    snapshot: dict[str, Any]
    compiler_hash: str
    items: tuple[CompiledItem, ...]


def compile_plan(
    *,
    product_category: str,
    reference_views: set[str],
    platform_slug: str,
    platform_version: int,
    platform_rules: dict[str, Any],
    category_slug: str,
    category_version: int,
    category_rules: dict[str, Any],
    brand_slug: str,
    brand_version: int,
    brand_rules: dict[str, Any],
    mode: str,
) -> CompiledPlan:
    if category_rules.get("category") != product_category:
        raise PlanCompilationError("Category pack does not match product category")
    if mode not in {"strict", "creative"}:
        raise PlanCompilationError("Unsupported truth mode")

    category_slots = category_rules.get("slots", {})
    copy_by_slot = brand_rules.get("copy", {})
    items: list[CompiledItem] = []
    for position, platform_slot in enumerate(platform_rules.get("slots", [])):
        slot = platform_slot["key"]
        category_slot = category_slots.get(slot)
        if category_slot is None:
            continue
        required_any = set(category_slot.get("required_reference_views", []))
        if mode == "strict" and required_any and not required_any.intersection(reference_views):
            choices = "/".join(sorted(required_any))
            raise PlanCompilationError(f"Strict mode requires one of these references: {choices}")

        authoritative_copy = copy_by_slot.get(slot) if platform_slot.get("allow_text") else None
        rules = {
            **platform_slot,
            "format": platform_rules["format"],
            "max_file_bytes": platform_rules["max_file_bytes"],
            "safe_margin": platform_rules["safe_margin"],
            "required_reference_views": sorted(required_any),
            "palette": brand_rules.get("palette", {}),
            "font": brand_rules.get("font"),
            "minimum_font_size": brand_rules.get("minimum_font_size", 24),
        }
        prompt = (
            f"Generate {platform_slot['label']} for commerce. Preserve product identity, "
            "color, material, logo and construction. Do not render text in the base image."
        )
        items.append(
            CompiledItem(
                position=len(items),
                slot=slot,
                label=platform_slot["label"],
                requested_view=platform_slot["view"],
                width=platform_slot["width"],
                height=platform_slot["height"],
                prompt=prompt,
                authoritative_copy=authoritative_copy,
                rules=rules,
            )
        )
    if not items:
        raise PlanCompilationError("No compatible image slots")

    snapshot = {
        "packs": {
            "platform": {"slug": platform_slug, "version": platform_version},
            "category": {"slug": category_slug, "version": category_version},
            "brand": {"slug": brand_slug, "version": brand_version},
        },
        "mode": mode,
        "items": [
            {
                "position": item.position,
                "slot": item.slot,
                "label": item.label,
                "requested_view": item.requested_view,
                "width": item.width,
                "height": item.height,
                "prompt": item.prompt,
                "authoritative_copy": item.authoritative_copy,
                "rules": item.rules,
            }
            for item in items
        ],
    }
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return CompiledPlan(
        snapshot=snapshot,
        compiler_hash=hashlib.sha256(canonical.encode()).hexdigest(),
        items=tuple(items),
    )
