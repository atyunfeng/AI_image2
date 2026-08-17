from io import BytesIO
from uuid import uuid4

import pytest
from PIL import Image

from aiimage.assets.models import Asset
from aiimage.assets.storage import InMemoryObjectStore
from aiimage.composition.service import create_composed_asset


@pytest.mark.asyncio
async def test_composed_asset_records_parent_and_operation(session_factory) -> None:
    store = InMemoryObjectStore()
    buffer = BytesIO()
    Image.new("RGB", (200, 100), "white").save(buffer, format="PNG")
    stored = await store.put(content=buffer.getvalue(), mime_type="image/png")
    async with session_factory() as session:
        parent = Asset(
            id=uuid4(),
            object_key=stored.object_key,
            sha256=stored.sha256,
            size_bytes=stored.size_bytes,
            mime_type=stored.mime_type,
        )
        session.add(parent)
        await session.flush()
        asset = await create_composed_asset(
            session,
            store,
            parent=parent,
            rules={
                "key": "detail_material",
                "format": "JPEG",
                "allow_text": True,
                "text_region": [100, 10, 190, 90],
                "minimum_font_size": 16,
                "palette": {"text": "#111111"},
            },
            authoritative_copy="Material",
        )
        assert asset.parent_asset_id == parent.id
        assert asset.derivation_operation == "platform_composition"
        assert asset.mime_type == "image/jpeg"
