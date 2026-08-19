from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore
from aiimage.quality.models import QualityCheck, QualityRun
from aiimage.quality.rules import inspect_structure
from aiimage.quality.schemas import QualityCheckResponse, QualityRunResponse


async def run_structural_quality(
    session: AsyncSession,
    store: ObjectStore,
    *,
    batch_id: UUID,
    output_asset: Asset,
    rules: dict,
) -> QualityRun:
    content = await store.get(object_key=output_asset.object_key)
    results = inspect_structure(content, output_asset.mime_type, rules)
    run = QualityRun(
        batch_id=batch_id,
        output_asset_id=output_asset.id,
        passed=not any(not result.passed and result.blocking for result in results),
    )
    session.add(run)
    await session.flush()
    session.add_all(
        [
            QualityCheck(
                run_id=run.id,
                code=result.code,
                passed=result.passed,
                blocking=result.blocking,
                expected=result.expected,
                measured=result.measured,
                message=result.message,
            )
            for result in results
        ]
        + [
            QualityCheck(
                run_id=run.id,
                code="semantic_human_review_required",
                passed=False,
                blocking=False,
                expected={
                    "checks": [
                        "product_identity",
                        "color_material",
                        "logo_text",
                        "visual_artifacts",
                    ]
                },
                measured={"automated_semantic_provider": None},
                message="结构检查已完成；商品语义质量仍需人工审核",
            )
        ]
    )
    return run


async def latest_quality_response(
    session: AsyncSession, batch_id: UUID
) -> QualityRunResponse | None:
    run = await session.scalar(
        select(QualityRun)
        .where(QualityRun.batch_id == batch_id)
        .order_by(desc(QualityRun.created_at))
        .limit(1)
    )
    if run is None:
        return None
    checks = list(
        (
            await session.scalars(
                select(QualityCheck)
                .where(QualityCheck.run_id == run.id)
                .order_by(QualityCheck.code)
            )
        ).all()
    )
    return QualityRunResponse(
        id=run.id,
        batch_id=run.batch_id,
        output_asset_id=run.output_asset_id,
        passed=run.passed,
        created_at=run.created_at,
        checks=[
            QualityCheckResponse(
                code=check.code,
                passed=check.passed,
                blocking=check.blocking,
                expected=check.expected,
                measured=check.measured,
                message=check.message,
            )
            for check in checks
        ],
    )


async def has_blocking_quality_failure(session: AsyncSession, batch_id: UUID) -> bool:
    run = await session.scalar(
        select(QualityRun)
        .where(QualityRun.batch_id == batch_id)
        .order_by(desc(QualityRun.created_at))
        .limit(1)
    )
    return run is not None and not run.passed
