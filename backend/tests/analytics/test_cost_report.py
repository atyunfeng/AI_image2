from aiimage.analytics.service import build_cost_report
from aiimage.auth.models import Role
from aiimage.auth.service import create_user
from aiimage.catalog.models import Product
from aiimage.models.models import ModelConfiguration
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus, StepStatus


async def test_cost_report_separates_currencies_and_filters_platform(session_factory) -> None:
    async with session_factory() as session:
        user = await create_user(
            session,
            email="costs@aiimage.local",
            password="Cost-Report-Password-2026",
            roles={Role.ADMIN},
        )
        product = Product(
            sku="COST-001",
            name="成本样品",
            category="apparel",
            created_by_user_id=user.id,
        )
        usd_model = ModelConfiguration(
            name="USD model",
            provider="mock",
            model_id="usd-v1",
            capabilities=["reference_to_image"],
            billing_currency="USD",
            created_by_user_id=user.id,
        )
        cny_model = ModelConfiguration(
            name="CNY model",
            provider="mock",
            model_id="cny-v1",
            capabilities=["reference_to_image"],
            billing_currency="CNY",
            created_by_user_id=user.id,
        )
        session.add_all([product, usd_model, cny_model])
        await session.flush()
        batches = []
        for model, platform in [(usd_model, "amazon-global"), (cny_model, "jd-cn")]:
            batch = GenerationBatch(
                product_id=product.id,
                model_configuration_id=model.id,
                requested_view="front",
                prompt="cost",
                width=1024,
                height=1024,
                status=BatchStatus.REVIEW_PENDING.value,
                input_snapshot={"pack_versions": {"platform": {"slug": platform}}},
                created_by_user_id=user.id,
            )
            session.add(batch)
            await session.flush()
            session.add(
                GenerationStep(
                    batch_id=batch.id,
                    idempotency_key=f"cost-{platform}",
                    status=StepStatus.SUCCEEDED.value,
                    estimated_cost_minor=125,
                )
            )
            batches.append(batch)
        await session.commit()

        report = await build_cost_report(session)
        assert [(item.currency, item.reported_cost_minor) for item in report.summaries] == [
            ("CNY", 125),
            ("USD", 125),
        ]
        amazon = await build_cost_report(session, platform_slug="amazon-global")
        assert len(amazon.breakdown) == 1
        assert amazon.breakdown[0].platform == "amazon-global"
        assert amazon.breakdown[0].sku == "COST-001"

