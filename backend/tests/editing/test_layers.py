from uuid import uuid4

from aiimage.editing.models import EditProject
from aiimage.editing.schemas import EditLayerCreate, EditLayerUpdate
from aiimage.editing.service import (
    EditValidationError,
    create_layer,
    duplicate_layer,
    reorder_layers,
    update_layer,
)


async def test_layer_lock_duplicate_and_reorder(session_factory) -> None:
    async with session_factory() as session:
        user_id = uuid4()
        project = EditProject(
            name="layers",
            product_id=uuid4(),
            source_batch_id=uuid4(),
            source_asset_id=uuid4(),
            created_by_user_id=user_id,
        )
        session.add(project)
        await session.commit()
        background = await create_layer(
            session,
            project_id=project.id,
            payload=EditLayerCreate(
                layer_type="background", name="BG", locked=True, content={"color": "#fff"}
            ),
            user_id=user_id,
        )
        text = await create_layer(
            session,
            project_id=project.id,
            payload=EditLayerCreate(
                layer_type="text",
                name="Title",
                opacity=80,
                content={"text": "新品", "region": [0, 0, 100, 50]},
            ),
            user_id=user_id,
        )
        try:
            await update_layer(
                session,
                project_id=project.id,
                layer_id=background.id,
                payload=EditLayerUpdate(content={"color": "#000"}),
                user_id=user_id,
            )
        except EditValidationError as error:
            assert "Unlock" in str(error)
        else:
            raise AssertionError("Expected locked layer protection")
        copy = await duplicate_layer(
            session, project_id=project.id, layer_id=text.id, user_id=user_id
        )
        reordered = await reorder_layers(
            session,
            project_id=project.id,
            layer_ids=[copy.id, text.id, background.id],
            user_id=user_id,
        )
        assert [layer.position for layer in reordered] == [1, 2, 3]
        assert copy.opacity == 80
