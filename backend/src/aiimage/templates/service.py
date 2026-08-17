from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.catalog.models import Product, ProductReference
from aiimage.templates.compiler import PlanCompilationError, compile_plan
from aiimage.templates.models import (
    PackKind,
    ProductionPlan,
    ProductionPlanItem,
    TemplatePack,
    TemplatePackVersion,
)
from aiimage.templates.presets import first_party_packs
from aiimage.templates.schemas import (
    CompilePlanRequest,
    ProductionPlanItemResponse,
    ProductionPlanResponse,
    TemplatePackResponse,
)


async def ensure_first_party_packs(session: AsyncSession) -> None:
    existing = set((await session.scalars(select(TemplatePack.slug))).all())
    for preset in first_party_packs():
        if preset["slug"] in existing:
            continue
        pack = TemplatePack(slug=preset["slug"], name=preset["name"], kind=preset["kind"])
        session.add(pack)
        await session.flush()
        session.add(
            TemplatePackVersion(
                pack_id=pack.id,
                version=1,
                rules=preset["rules"],
                source="first_party_default",
            )
        )
    await session.commit()


async def list_published_packs(session: AsyncSession) -> list[TemplatePackResponse]:
    await ensure_first_party_packs(session)
    rows = (
        await session.execute(
            select(TemplatePack, TemplatePackVersion)
            .join(TemplatePackVersion, TemplatePackVersion.pack_id == TemplatePack.id)
            .where(TemplatePackVersion.status == "published")
            .order_by(TemplatePack.kind, TemplatePack.slug, TemplatePackVersion.version.desc())
        )
    ).all()
    return [
        TemplatePackResponse(
            id=pack.id,
            version_id=version.id,
            slug=pack.slug,
            name=pack.name,
            kind=pack.kind,
            version=version.version,
            status=version.status,
            rules=version.rules,
            source=version.source,
            published_at=version.published_at,
        )
        for pack, version in rows
    ]


async def _load_pack_version(
    session: AsyncSession, version_id: UUID, expected_kind: PackKind
) -> tuple[TemplatePack, TemplatePackVersion]:
    row = (
        await session.execute(
            select(TemplatePack, TemplatePackVersion)
            .join(TemplatePackVersion, TemplatePackVersion.pack_id == TemplatePack.id)
            .where(TemplatePackVersion.id == version_id)
        )
    ).one_or_none()
    if row is None or row[0].kind != expected_kind.value:
        raise PlanCompilationError(f"Missing {expected_kind.value} pack version")
    return row[0], row[1]


def to_plan_response(
    plan: ProductionPlan, items: list[ProductionPlanItem]
) -> ProductionPlanResponse:
    return ProductionPlanResponse(
        id=plan.id,
        product_id=plan.product_id,
        mode=plan.mode,
        compiler_hash=plan.compiler_hash,
        compiled_snapshot=plan.compiled_snapshot,
        created_at=plan.created_at,
        items=[
            ProductionPlanItemResponse(
                id=item.id,
                position=item.position,
                slot=item.slot,
                label=item.label,
                requested_view=item.requested_view,
                width=item.width,
                height=item.height,
                prompt=item.prompt,
                authoritative_copy=item.authoritative_copy,
                rules=item.rules,
            )
            for item in sorted(items, key=lambda value: value.position)
        ],
    )


async def create_production_plan(
    session: AsyncSession, *, payload: CompilePlanRequest, user_id: UUID
) -> ProductionPlanResponse:
    await ensure_first_party_packs(session)
    product = await session.get(Product, payload.product_id)
    if product is None:
        raise PlanCompilationError("Product not found")
    platform, platform_version = await _load_pack_version(
        session, payload.platform_pack_version_id, PackKind.PLATFORM
    )
    category, category_version = await _load_pack_version(
        session, payload.category_pack_version_id, PackKind.CATEGORY
    )
    brand, brand_version = await _load_pack_version(
        session, payload.brand_pack_version_id, PackKind.BRAND
    )
    reference_views = set(
        (
            await session.scalars(
                select(ProductReference.view).where(ProductReference.product_id == product.id)
            )
        ).all()
    )
    compiled = compile_plan(
        product_category=product.category,
        reference_views=reference_views,
        platform_slug=platform.slug,
        platform_version=platform_version.version,
        platform_rules=platform_version.rules,
        category_slug=category.slug,
        category_version=category_version.version,
        category_rules=category_version.rules,
        brand_slug=brand.slug,
        brand_version=brand_version.version,
        brand_rules=brand_version.rules,
        mode=payload.mode,
    )
    plan = ProductionPlan(
        product_id=product.id,
        platform_pack_version_id=platform_version.id,
        category_pack_version_id=category_version.id,
        brand_pack_version_id=brand_version.id,
        mode=payload.mode,
        compiled_snapshot=compiled.snapshot,
        compiler_hash=compiled.compiler_hash,
        created_by_user_id=user_id,
    )
    session.add(plan)
    await session.flush()
    items = [
        ProductionPlanItem(
            plan_id=plan.id,
            position=item.position,
            slot=item.slot,
            label=item.label,
            requested_view=item.requested_view,
            width=item.width,
            height=item.height,
            prompt=item.prompt,
            authoritative_copy=item.authoritative_copy,
            rules=item.rules,
        )
        for item in compiled.items
    ]
    session.add_all(items)
    await session.commit()
    return to_plan_response(plan, items)


async def get_production_plan(
    session: AsyncSession, plan_id: UUID
) -> ProductionPlanResponse | None:
    plan = await session.get(ProductionPlan, plan_id)
    if plan is None:
        return None
    items = list(
        (
            await session.scalars(
                select(ProductionPlanItem).where(ProductionPlanItem.plan_id == plan.id)
            )
        ).all()
    )
    return to_plan_response(plan, items)
