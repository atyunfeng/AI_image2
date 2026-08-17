from io import BytesIO
from uuid import uuid4

from PIL import Image

from aiimage.assets.models import Asset
from aiimage.assets.storage import InMemoryObjectStore
from aiimage.editing.images import select_by_corner_color
from aiimage.editing.models import EditProject, EditRevision
from aiimage.editing.service import EditValidationError, create_selection


def test_corner_color_selection_separates_foreground_and_background() -> None:
    image = Image.new("RGB", (12, 12), "white")
    for x in range(4, 8):
        for y in range(4, 8):
            image.putpixel((x, y), (20, 30, 40))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    foreground, width, height = select_by_corner_color(
        buffer.getvalue(), foreground=True, threshold=30
    )
    background, _, _ = select_by_corner_color(buffer.getvalue(), foreground=False, threshold=30)

    with Image.open(BytesIO(foreground)) as mask:
        assert mask.getpixel((6, 6)) == 255
        assert mask.getpixel((0, 0)) == 0
    with Image.open(BytesIO(background)) as mask:
        assert mask.getpixel((6, 6)) == 0
        assert mask.getpixel((0, 0)) == 255
    assert (width, height) == (12, 12)


async def test_semantic_selection_requires_segment_provider(session_factory, png_bytes) -> None:
    store = InMemoryObjectStore()
    stored = await store.put(content=png_bytes, mime_type="image/png")
    async with session_factory() as session:
        asset = Asset(
            object_key=stored.object_key,
            sha256=stored.sha256,
            size_bytes=stored.size_bytes,
            mime_type=stored.mime_type,
        )
        session.add(asset)
        await session.flush()
        project = EditProject(
            name="selection",
            product_id=uuid4(),
            source_batch_id=uuid4(),
            source_asset_id=asset.id,
            created_by_user_id=uuid4(),
        )
        session.add(project)
        await session.flush()
        revision = EditRevision(
            project_id=project.id,
            version=0,
            operation="source",
            status="ready",
            source_asset_id=asset.id,
            output_asset_id=asset.id,
            parameters={},
            created_by_user_id=project.created_by_user_id,
        )
        session.add(revision)
        await session.commit()

        try:
            await create_selection(
                session,
                store,
                project_id=project.id,
                revision_id=revision.id,
                selection_type="person",
                threshold=42,
                user_id=project.created_by_user_id,
            )
        except EditValidationError as error:
            assert "segment provider" in str(error)
        else:
            raise AssertionError("Expected semantic selection provider validation")
