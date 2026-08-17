import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import UUID

from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore
from aiimage.auth.models import User  # noqa: F401 - registers worker foreign-key metadata
from aiimage.catalog.models import ProductReference
from aiimage.models.domain import Capability, GenerationRequest, ReferenceImage
from aiimage.models.models import ModelConfiguration
from aiimage.providers.registry import ProviderRegistry
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus, StepStatus

LEASE_DURATION = timedelta(minutes=5)
logger = logging.getLogger(__name__)
TERMINAL_STEP_STATUSES = {
    StepStatus.SUCCEEDED.value,
    StepStatus.FAILED.value,
    StepStatus.CANCELED.value,
}


@dataclass(frozen=True)
class WorkerContext:
    session_factory: async_sessionmaker[AsyncSession]
    object_store: ObjectStore
    provider_registry: ProviderRegistry


class StructuralQAError(RuntimeError):
    pass


def _validate_output(content: bytes, mime_type: str, expected_sha256: str) -> None:
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if actual_sha256 != expected_sha256:
        raise StructuralQAError("output_sha256_mismatch")
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
        with Image.open(BytesIO(content)) as image:
            if image.width <= 0 or image.height <= 0:
                raise StructuralQAError("output_invalid_dimensions")
            expected_format = {
                "image/png": "PNG",
                "image/jpeg": "JPEG",
                "image/webp": "WEBP",
            }.get(mime_type)
            if expected_format is None or image.format != expected_format:
                raise StructuralQAError("output_mime_mismatch")
    except UnidentifiedImageError as exc:
        raise StructuralQAError("output_decode_failed") from exc


async def _lease_step(
    step_id: UUID,
    worker_id: str,
    context: WorkerContext,
) -> tuple[GenerationStep, GenerationBatch, ModelConfiguration] | None:
    now = datetime.now(UTC)
    async with context.session_factory() as session:
        step = await session.scalar(
            select(GenerationStep)
            .where(GenerationStep.id == step_id)
            .with_for_update(skip_locked=True)
        )
        if step is None or step.status in TERMINAL_STEP_STATUSES:
            return None
        lease_is_expired = step.lease_expires_at is None or step.lease_expires_at <= now
        if step.status == StepStatus.RUNNING.value and not lease_is_expired:
            return None
        if step.status not in {
            StepStatus.QUEUED.value,
            StepStatus.RETRY_QUEUED.value,
            StepStatus.RUNNING.value,
        }:
            return None
        batch = await session.get(GenerationBatch, step.batch_id)
        if batch is None:
            return None
        configuration = await session.get(ModelConfiguration, batch.model_configuration_id)
        if configuration is None or not configuration.is_enabled:
            step.status = StepStatus.FAILED.value
            step.error_classification = "model_unavailable"
            batch.status = BatchStatus.FAILED.value
            await session.commit()
            return None
        step.status = StepStatus.RUNNING.value
        step.lease_owner = worker_id
        step.lease_expires_at = now + LEASE_DURATION
        step.attempt_count += 1
        batch.status = BatchStatus.RUNNING.value
        await session.commit()
        return step, batch, configuration


async def _load_references(
    batch: GenerationBatch,
    context: WorkerContext,
) -> list[ReferenceImage]:
    reference_ids = [UUID(value) for value in batch.input_snapshot.get("reference_ids", [])]
    if not reference_ids:
        return []
    async with context.session_factory() as session:
        references = list(
            (
                await session.scalars(
                    select(ProductReference).where(ProductReference.id.in_(reference_ids))
                )
            ).all()
        )
        assets = {
            asset.id: asset
            for asset in (
                await session.scalars(
                    select(Asset).where(
                        Asset.id.in_([reference.asset_id for reference in references])
                    )
                )
            ).all()
        }
    images = []
    for reference in references:
        asset = assets[reference.asset_id]
        images.append(
            ReferenceImage(
                content=await context.object_store.get(object_key=asset.object_key),
                mime_type=asset.mime_type,
            )
        )
    return images


async def _mark_failed(step_id: UUID, classification: str, context: WorkerContext) -> None:
    async with context.session_factory() as session:
        step = await session.get(GenerationStep, step_id)
        if step is None or step.status in TERMINAL_STEP_STATUSES:
            return
        batch = await session.get(GenerationBatch, step.batch_id)
        step.status = StepStatus.FAILED.value
        step.error_classification = classification
        step.lease_owner = None
        step.lease_expires_at = None
        if batch is not None:
            batch.status = BatchStatus.FAILED.value
        await session.commit()


async def execute_step(step_id: UUID, worker_id: str, context: WorkerContext) -> bool:
    leased = await _lease_step(step_id, worker_id, context)
    if leased is None:
        return False
    step, batch, configuration = leased
    try:
        references = await _load_references(batch, context)
        provider = context.provider_registry.get(configuration)
        result = await provider.generate(
            GenerationRequest(
                idempotency_key=step.idempotency_key,
                capability=Capability.REFERENCE_TO_IMAGE,
                prompt=batch.prompt,
                reference_images=references,
                width=batch.width,
                height=batch.height,
                parameters={"requested_view": batch.requested_view, "mode": batch.mode},
            )
        )
        _validate_output(result.content, result.mime_type, result.content_sha256)
        stored = await context.object_store.put(
            content=result.content,
            mime_type=result.mime_type,
        )
    except StructuralQAError as exc:
        await _mark_failed(step_id, str(exc), context)
        return False
    except Exception:
        logger.exception("Provider execution failed for generation step %s", step_id)
        await _mark_failed(step_id, "provider_error", context)
        return False

    async with context.session_factory() as session:
        current = await session.get(GenerationStep, step_id)
        if current is None or current.status != StepStatus.RUNNING.value:
            return False
        asset = await session.scalar(select(Asset).where(Asset.sha256 == stored.sha256))
        if asset is None:
            asset = Asset(
                object_key=stored.object_key,
                sha256=stored.sha256,
                size_bytes=stored.size_bytes,
                mime_type=stored.mime_type,
            )
            session.add(asset)
            await session.flush()
        current.status = StepStatus.SUCCEEDED.value
        current.provider_request_id = result.provider_request_id
        current.output_asset_id = asset.id
        current.estimated_cost_minor = result.estimated_cost_minor
        current.lease_owner = None
        current.lease_expires_at = None
        current.error_classification = None
        current_batch = await session.get(GenerationBatch, current.batch_id)
        if current_batch is not None:
            current_batch.status = BatchStatus.QA_PENDING.value
            current_batch.status = BatchStatus.REVIEW_PENDING.value
        await session.commit()
    return True
