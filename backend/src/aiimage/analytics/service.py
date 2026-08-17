from collections import defaultdict
from datetime import UTC, date, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.analytics.schemas import (
    CostBreakdownRow,
    CostReportResponse,
    CostSummary,
    DailyCostPoint,
    FailureClassRow,
    OperationAlert,
    OperationsReportResponse,
)
from aiimage.catalog.models import Product
from aiimage.models.models import ModelConfiguration
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus, StepStatus


def _platform(batch: GenerationBatch) -> str:
    versions = batch.input_snapshot.get("pack_versions", {})
    platform = versions.get("platform", {}) if isinstance(versions, dict) else {}
    return str(platform.get("slug") or "unassigned")


def _base_statement(
    *,
    date_from: date | None,
    date_to: date | None,
    provider: str | None,
    sku: str | None,
    status: str | None = None,
):
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
    if status:
        statement = statement.where(GenerationBatch.status == status)
    return statement


async def build_cost_report(
    session: AsyncSession,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    provider: str | None = None,
    platform_slug: str | None = None,
    sku: str | None = None,
) -> CostReportResponse:
    statement = _base_statement(
        date_from=date_from, date_to=date_to, provider=provider, sku=sku
    )
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
                average_cost_minor=value["cost"] / value["tasks"] if value["tasks"] else 0,
                success_rate=value["succeeded"] / value["tasks"] if value["tasks"] else 0,
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


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


async def build_operations_report(
    session: AsyncSession,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    provider: str | None = None,
    platform_slug: str | None = None,
    sku: str | None = None,
    status: str | None = None,
) -> OperationsReportResponse:
    statement = _base_statement(
        date_from=date_from,
        date_to=date_to,
        provider=provider,
        sku=sku,
        status=status,
    )
    rows = [
        row
        for row in (await session.execute(statement)).all()
        if not platform_slug or _platform(row[1]) == platform_slug
    ]
    batches = [row[1] for row in rows]
    steps = [row[0] for row in rows]
    queued = sum(
        batch.status in {BatchStatus.QUEUED.value, BatchStatus.RETRY_QUEUED.value}
        for batch in batches
    )
    running = sum(batch.status == BatchStatus.RUNNING.value for batch in batches)
    review = sum(batch.status == BatchStatus.REVIEW_PENDING.value for batch in batches)
    failed = sum(batch.status == BatchStatus.FAILED.value for batch in batches)
    succeeded = sum(step.status == StepStatus.SUCCEEDED.value for step in steps)
    retry_calls = sum(max(0, step.attempt_count - 1) for step in steps)
    latencies = [
        (step.completed_at - step.started_at).total_seconds() * 1000
        for step in steps
        if step.started_at is not None and step.completed_at is not None
    ]
    failures: dict[str, int] = defaultdict(int)
    costs: dict[str, dict[str, int]] = defaultdict(
        lambda: {"tasks": 0, "succeeded": 0, "failed": 0, "cost": 0}
    )
    for step, _, model, _ in rows:
        if step.error_classification:
            failures[step.error_classification] += 1
        bucket = costs[model.billing_currency]
        bucket["tasks"] += 1
        bucket["succeeded"] += int(step.status == StepStatus.SUCCEEDED.value)
        bucket["failed"] += int(
            step.status in {StepStatus.FAILED.value, StepStatus.CANCELED.value}
        )
        bucket["cost"] += step.estimated_cost_minor
    alerts: list[OperationAlert] = []
    if queued >= 20:
        alerts.append(
            OperationAlert(
                code="queue_depth",
                severity="warning",
                title="生成队列积压",
                detail=f"当前有 {queued} 个排队任务。",
                action_url="/batches?status=queued",
            )
        )
    if failed:
        alerts.append(
            OperationAlert(
                code="generation_failures",
                severity="critical",
                title="存在失败任务",
                detail=f"筛选范围内有 {failed} 个失败批次。",
                action_url="/batches?status=failed",
            )
        )
    if review >= 20:
        alerts.append(
            OperationAlert(
                code="review_backlog",
                severity="warning",
                title="审核队列积压",
                detail=f"当前有 {review} 个待审核批次。",
                action_url="/review",
            )
        )
    return OperationsReportResponse(
        generated_at=datetime.now(UTC),
        queued_count=queued,
        running_count=running,
        review_pending_count=review,
        failed_count=failed,
        total_calls=len(steps),
        succeeded_calls=succeeded,
        retry_calls=retry_calls,
        success_rate=succeeded / len(steps) if steps else 0,
        retry_rate=retry_calls / len(steps) if steps else 0,
        latency_p50_ms=_percentile(latencies, 0.5),
        latency_p95_ms=_percentile(latencies, 0.95),
        failure_classes=[
            FailureClassRow(classification=classification, count=count)
            for classification, count in sorted(
                failures.items(), key=lambda item: (-item[1], item[0])
            )
        ],
        cost_groups=[
            CostSummary(
                currency=currency,
                task_count=value["tasks"],
                succeeded_count=value["succeeded"],
                failed_count=value["failed"],
                reported_cost_minor=value["cost"],
                average_cost_minor=value["cost"] / value["tasks"] if value["tasks"] else 0,
                success_rate=value["succeeded"] / value["tasks"] if value["tasks"] else 0,
            )
            for currency, value in sorted(costs.items())
        ],
        alerts=alerts,
    )
