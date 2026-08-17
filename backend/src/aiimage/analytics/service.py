from collections import defaultdict
from datetime import UTC, date, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.analytics.schemas import (
    CostBreakdownRow,
    CostReportResponse,
    CostSummary,
    DailyCostPoint,
)
from aiimage.catalog.models import Product
from aiimage.models.models import ModelConfiguration
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import StepStatus


def _platform(batch: GenerationBatch) -> str:
    versions = batch.input_snapshot.get("pack_versions", {})
    platform = versions.get("platform", {}) if isinstance(versions, dict) else {}
    return str(platform.get("slug") or "unassigned")


async def build_cost_report(
    session: AsyncSession,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    provider: str | None = None,
    platform_slug: str | None = None,
    sku: str | None = None,
) -> CostReportResponse:
    statement = (
        select(GenerationStep, GenerationBatch, ModelConfiguration, Product)
        .join(GenerationBatch, GenerationBatch.id == GenerationStep.batch_id)
        .join(ModelConfiguration, ModelConfiguration.id == GenerationBatch.model_configuration_id)
        .join(Product, Product.id == GenerationBatch.product_id)
    )
    if date_from:
        statement = statement.where(
            GenerationBatch.created_at >= datetime.combine(date_from, time.min, tzinfo=UTC)
        )
    if date_to:
        statement = statement.where(
            GenerationBatch.created_at <= datetime.combine(date_to, time.max, tzinfo=UTC)
        )
    if provider:
        statement = statement.where(ModelConfiguration.provider == provider)
    if sku:
        statement = statement.where(Product.sku == sku.strip().upper())

    summary: dict[str, dict[str, int]] = defaultdict(
        lambda: {"tasks": 0, "succeeded": 0, "failed": 0, "cost": 0}
    )
    daily: dict[tuple[date, str], dict[str, int]] = defaultdict(
        lambda: {"tasks": 0, "cost": 0}
    )
    breakdown: dict[tuple[str, str, str, str, str], dict[str, int]] = defaultdict(
        lambda: {"tasks": 0, "succeeded": 0, "failed": 0, "cost": 0}
    )
    for step, batch, model, product in (await session.execute(statement)).all():
        platform = _platform(batch)
        if platform_slug and platform != platform_slug:
            continue
        currency = model.billing_currency
        succeeded = int(step.status == StepStatus.SUCCEEDED.value)
        failed = int(step.status in {StepStatus.FAILED.value, StepStatus.CANCELED.value})
        cost = step.estimated_cost_minor
        summary[currency]["tasks"] += 1
        summary[currency]["succeeded"] += succeeded
        summary[currency]["failed"] += failed
        summary[currency]["cost"] += cost
        day_key = (batch.created_at.date(), currency)
        daily[day_key]["tasks"] += 1
        daily[day_key]["cost"] += cost
        key = (model.provider, model.name, platform, product.sku, currency)
        breakdown[key]["tasks"] += 1
        breakdown[key]["succeeded"] += succeeded
        breakdown[key]["failed"] += failed
        breakdown[key]["cost"] += cost

    return CostReportResponse(
        generated_at=datetime.now(UTC),
        cost_basis="provider_reported_or_estimated",
        summaries=[
            CostSummary(
                currency=currency,
                task_count=value["tasks"],
                succeeded_count=value["succeeded"],
                failed_count=value["failed"],
                reported_cost_minor=value["cost"],
                average_cost_minor=(value["cost"] / value["tasks"] if value["tasks"] else 0),
                success_rate=(value["succeeded"] / value["tasks"] if value["tasks"] else 0),
            )
            for currency, value in sorted(summary.items())
        ],
        daily=[
            DailyCostPoint(
                date=day,
                currency=currency,
                task_count=value["tasks"],
                reported_cost_minor=value["cost"],
            )
            for (day, currency), value in sorted(daily.items())
        ],
        breakdown=[
            CostBreakdownRow(
                provider=key[0],
                model=key[1],
                platform=key[2],
                sku=key[3],
                currency=key[4],
                task_count=value["tasks"],
                succeeded_count=value["succeeded"],
                failed_count=value["failed"],
                reported_cost_minor=value["cost"],
            )
            for key, value in sorted(breakdown.items())
        ],
    )

