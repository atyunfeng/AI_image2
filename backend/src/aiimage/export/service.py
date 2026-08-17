import hashlib
import json
from io import BytesIO
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore
from aiimage.audit.service import record_audit_event
from aiimage.auth.models import User
from aiimage.catalog.models import Product, ProductReference
from aiimage.export.models import ExportRecord
from aiimage.models.models import ModelConfiguration
from aiimage.review.models import ReviewDecision
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus


class ExportConflictError(RuntimeError):
    pass


async def build_export_zip(
    session: AsyncSession,
    store: ObjectStore,
    *,
    batch_id: UUID,
    user_id: UUID | None = None,
) -> bytes:
    batch = await session.get(GenerationBatch, batch_id)
    if batch is None:
        raise LookupError(batch_id)
    if batch.status not in {BatchStatus.APPROVED.value, BatchStatus.EXPORTED.value}:
        raise ExportConflictError("Only approved batches can be exported")
    decision = await session.scalar(
        select(ReviewDecision)
        .where(
            ReviewDecision.batch_id == batch.id,
            ReviewDecision.decision == "approve",
        )
        .order_by(desc(ReviewDecision.created_at), desc(ReviewDecision.id))
        .limit(1)
    )
    if decision is None or decision.output_asset_id is None:
        raise ExportConflictError("Approved output is missing")
    step = await session.get(GenerationStep, decision.step_id)
    output = await session.get(Asset, decision.output_asset_id)
    product = await session.get(Product, batch.product_id)
    model = await session.get(ModelConfiguration, batch.model_configuration_id)
    reviewer = await session.get(User, decision.reviewer_user_id)
    if step is None or output is None or product is None or model is None or reviewer is None:
        raise ExportConflictError("Export provenance is incomplete")
    reference_ids = [UUID(value) for value in batch.input_snapshot.get("reference_ids", [])]
    input_hashes: list[str] = []
    if reference_ids:
        references = list(
            (
                await session.scalars(
                    select(ProductReference).where(ProductReference.id.in_(reference_ids))
                )
            ).all()
        )
        assets = list(
            (
                await session.scalars(
                    select(Asset).where(
                        Asset.id.in_([reference.asset_id for reference in references])
                    )
                )
            ).all()
        )
        input_hashes = sorted(asset.sha256 for asset in assets)
    extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[
        output.mime_type
    ]
    filename = f"{product.sku}-{batch.requested_view}.{extension}"
    manifest = {
        "schema_version": 1,
        "batch_id": str(batch.id),
        "product": {"id": str(product.id), "sku": product.sku},
        "input_asset_sha256": input_hashes,
        "truth_anchor_version": batch.input_snapshot.get("truth_anchor_version"),
        "generation": {
            "provider": model.provider,
            "model_id": model.model_id,
            "parameters": {
                "prompt": batch.prompt,
                "width": batch.width,
                "height": batch.height,
                "requested_view": batch.requested_view,
                "mode": batch.mode,
            },
            "provider_request_id": step.provider_request_id,
            "cost_minor": step.estimated_cost_minor,
        },
        "review": {
            "reviewer": reviewer.email,
            "decision_at": decision.created_at.isoformat(),
        },
        "assets": [
            {
                "filename": filename,
                "sha256": output.sha256,
                "mime_type": output.mime_type,
                "size_bytes": output.size_bytes,
            }
        ],
    }
    image = await store.get(object_key=output.object_key)
    archive_buffer = BytesIO()
    with ZipFile(archive_buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.writestr(filename, image)
    content = archive_buffer.getvalue()
    stored = await store.put(content=content, mime_type="application/zip")
    archive_asset = await session.scalar(select(Asset).where(Asset.sha256 == stored.sha256))
    if archive_asset is None:
        archive_asset = Asset(
            object_key=stored.object_key,
            sha256=stored.sha256,
            size_bytes=stored.size_bytes,
            mime_type=stored.mime_type,
            parent_asset_id=output.id,
            derivation_operation="approved_export_zip",
            derivation_parameters={"batch_id": str(batch.id)},
        )
        session.add(archive_asset)
        await session.flush()
    manifest_sha256 = hashlib.sha256(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    actor_id = user_id or decision.reviewer_user_id
    record = ExportRecord(
        batch_id=batch.id,
        archive_asset_id=archive_asset.id,
        manifest_sha256=manifest_sha256,
        created_by_user_id=actor_id,
    )
    session.add(record)
    await record_audit_event(
        session,
        event_type="batch.exported",
        actor_user_id=actor_id,
        details={
            "batch_id": str(batch.id),
            "archive_asset_id": str(archive_asset.id),
            "manifest_sha256": manifest_sha256,
        },
    )
    if batch.status == BatchStatus.APPROVED.value:
        batch.status = BatchStatus.EXPORTED.value
    await session.commit()
    return content


async def list_export_records(session: AsyncSession, batch_id: UUID) -> list[ExportRecord]:
    return list(
        (
            await session.scalars(
                select(ExportRecord)
                .where(ExportRecord.batch_id == batch_id)
                .order_by(ExportRecord.created_at.desc(), ExportRecord.id.desc())
            )
        ).all()
    )
