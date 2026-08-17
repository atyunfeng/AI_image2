from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.editing.models import EditProject, EditRevision
from aiimage.editing.schemas import EditProjectResponse, EditRevisionResponse
from aiimage.workflow.models import GenerationBatch, GenerationStep


class EditValidationError(ValueError):
    pass


async def create_edit_project(
    session: AsyncSession,
    *,
    source_batch_id: UUID,
    name: str | None,
    user_id: UUID,
) -> EditProject:
    batch = await session.get(GenerationBatch, source_batch_id)
    if batch is None:
        raise EditValidationError("Source batch was not found")
    step = await session.scalar(
        select(GenerationStep)
        .where(GenerationStep.batch_id == batch.id, GenerationStep.output_asset_id.is_not(None))
        .order_by(desc(GenerationStep.attempt_count))
        .limit(1)
    )
    if step is None or step.output_asset_id is None:
        raise EditValidationError("Source batch does not have a generated output")
    project = EditProject(
        name=(name or f"Edit {str(batch.id)[:8]}").strip(),
        product_id=batch.product_id,
        source_batch_id=batch.id,
        source_asset_id=step.output_asset_id,
        created_by_user_id=user_id,
    )
    session.add(project)
    await session.flush()
    root = EditRevision(
        project_id=project.id,
        version=0,
        snapshot_label="原始生成图",
        operation="source",
        status="ready",
        source_asset_id=step.output_asset_id,
        output_asset_id=step.output_asset_id,
        parameters={},
        created_by_user_id=user_id,
    )
    session.add(root)
    await session.commit()
    await session.refresh(project)
    return project


async def next_version(session: AsyncSession, project_id: UUID) -> int:
    current = await session.scalar(
        select(func.max(EditRevision.version)).where(EditRevision.project_id == project_id)
    )
    return int(current or 0) + 1


async def project_response(
    session: AsyncSession, project: EditProject
) -> EditProjectResponse:
    revisions = list(
        (
            await session.scalars(
                select(EditRevision)
                .where(EditRevision.project_id == project.id)
                .order_by(EditRevision.version)
            )
        ).all()
    )
    batches = {
        batch.edit_revision_id: batch.id
        for batch in (
            await session.scalars(
                select(GenerationBatch).where(
                    GenerationBatch.edit_revision_id.in_([revision.id for revision in revisions])
                )
            )
        ).all()
        if batch.edit_revision_id is not None
    }
    return EditProjectResponse(
        id=project.id,
        name=project.name,
        product_id=project.product_id,
        source_batch_id=project.source_batch_id,
        source_asset_id=project.source_asset_id,
        created_at=project.created_at,
        revisions=[
            EditRevisionResponse(
                id=revision.id,
                project_id=revision.project_id,
                parent_revision_id=revision.parent_revision_id,
                version=revision.version,
                snapshot_label=revision.snapshot_label,
                operation=revision.operation,
                capability=revision.capability,
                status=revision.status,
                source_asset_id=revision.source_asset_id,
                mask_asset_id=revision.mask_asset_id,
                output_asset_id=revision.output_asset_id,
                prompt=revision.prompt,
                parameters=revision.parameters,
                batch_id=batches.get(revision.id),
                created_at=revision.created_at,
            )
            for revision in revisions
        ],
    )
