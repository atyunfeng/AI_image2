from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore
from aiimage.composition.text import TextLayer, render_text_layers


async def create_composed_asset(
    session: AsyncSession,
    store: ObjectStore,
    *,
    parent: Asset,
    rules: dict[str, Any],
    authoritative_copy: str | None,
) -> Asset:
    layers: list[TextLayer] = []
    text_region = rules.get("text_region")
    if authoritative_copy:
        if not rules.get("allow_text") or not text_region:
            raise ValueError("Authoritative copy is not allowed for this slot")
        layers.append(
            TextLayer(
                text=authoritative_copy,
                region=tuple(text_region),
                font_size=max(32, int(rules.get("minimum_font_size", 24))),
                color=rules.get("palette", {}).get("text", "#16181D"),
            )
        )
    source = await store.get(object_key=parent.object_key)
    content, mime_type = render_text_layers(
        source, layers, output_format=rules.get("format", "PNG")
    )
    stored = await store.put(content=content, mime_type=mime_type)
    existing = await session.scalar(select(Asset).where(Asset.sha256 == stored.sha256))
    if existing is not None:
        return existing
    derivative = Asset(
        object_key=stored.object_key,
        sha256=stored.sha256,
        size_bytes=stored.size_bytes,
        mime_type=stored.mime_type,
        parent_asset_id=parent.id,
        derivation_operation="platform_composition",
        derivation_parameters={
            "slot": rules.get("key"),
            "format": rules.get("format", "PNG"),
            "text": authoritative_copy,
            "text_region": text_region,
        },
    )
    session.add(derivative)
    await session.flush()
    return derivative
