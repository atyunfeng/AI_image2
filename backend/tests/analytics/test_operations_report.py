from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aiimage.analytics.service import build_operations_report
from aiimage.catalog.models import Product
from aiimage.models.models import ModelConfiguration
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus, StepStatus


async def test_operations_report_aggregates_latency_retry_failures_and_alerts(session_factory) -> None:
    async with session_factory() as session:
        user_id = uuid4()
        product = Product(
            sku="OPS-001", name="Operations", category="other", created_by_user_id=user_id
        )
        model = ModelConfiguration(
            name="Ops mock",
            provider="mock",
            model_id="ops",
            billing_currency="USD",
            capabilities=["reference_to_image"],
            created_by_user_id=user_id,
        )
        session.add_all([product, model])
        await session.flush()
        now = datetime.now(UTC)
        succeeded = GenerationBatch(
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            prompt="success",
            width=512,
            height=512,
            status=BatchStatus.APPROVED.value,
            input_snapshot={"pack_versions": {"platform": {"slug": "amazon-global"}}},
            created_by_user_id=user_id,
        )
        failed = GenerationBatch(
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            prompt="failure",
            width=512,
            height=512,
            status=BatchStatus.FAILED.value,
            input_snapshot={"pack_versions": {"platform": {"slug": "amazon-global"}}},
            created_by_user_id=user_id,
        )
        session.add_all([succeeded, failed])
        await session.flush()
        session.add_all(
            [
                GenerationStep(
                    batch_id=succeeded.id,
                    idempotency_key="ops-success",
                    status=StepStatus.SUCCEEDED.value,
                    attempt_count=1,
                    started_at=now,
                    completed_at=now + timedelta(milliseconds=100),
                    estimated_cost_minor=20,
                ),
                GenerationStep(
                    batch_id=failed.id,
                    idempotency_key="ops-failed",
                    status=StepStatus.FAILED.value,
                    attempt_count=3,
                    started_at=now,
                    completed_at=now + timedelta(milliseconds=500),
                    error_classification="provider_error",
                    estimated_cost_minor=10,
                ),
            ]
        )
        await session.commit()

        report = await build_operations_report(
            session, platform_slug="amazon-global", provider="mock"
        )

        assert report.total_calls == 2
        assert report.success_rate == 0.5
        assert report.retry_calls == 2
        assert report.latency_p95_ms == 500
        assert report.failure_classes[0].classification == "provider_error"
        assert report.alerts[0].code == "generation_failures"
