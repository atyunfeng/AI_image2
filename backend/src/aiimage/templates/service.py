from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.audit.service import record_audit_event
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
    ManagedTemplatePackResponse,
    ProductionPlanItemResponse,
    ProductionPlanResponse,
    TemplatePackCreate,
    TemplatePackResponse,
    TemplatePackVersionCreate,
    TemplatePackVersionResponse,
)


class DuplicatePackSlugError(RuntimeError):
    pass


class PackManagementError(RuntimeError):
    pass


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
                published_at=datetime.now(UTC),
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


def _version_response(version: TemplatePackVersion) -> TemplatePackVersionResponse:
    return TemplatePackVersionResponse(
        id=version.id,
        version=version.version,
        status=version.status,
        rules=version.rules,
        source=version.source,
        published_at=version.published_at,
    )


async def list_managed_packs(session: AsyncSession) -> list[ManagedTemplatePackResponse]:
    await ensure_first_party_packs(session)
    packs = list((await session.scalars(select(TemplatePack).order_by(TemplatePack.kind, TemplatePack.slug))).all())
    versions = list(
        (
            await session.scalars(
                select(TemplatePackVersion).order_by(
                    TemplatePackVersion.pack_id, TemplatePackVersion.version.desc()
                )
            )
        ).all()
    )
    by_pack: dict[UUID, list[TemplatePackVersionResponse]] = {}
    for version in versions:
        by_pack.setdefault(version.pack_id, []).append(_version_response(version))
    return [
        ManagedTemplatePackResponse(
            id=pack.id,
            slug=pack.slug,
            name=pack.name,
            kind=pack.kind,
            versions=by_pack.get(pack.id, []),
        )
        for pack in packs
    ]


async def create_template_pack(
    session: AsyncSession, *, payload: TemplatePackCreate, user_id: UUID
) -> ManagedTemplatePackResponse:
    pack = TemplatePack(slug=payload.slug, name=payload.name.strip(), kind=payload.kind.value)
    session.add(pack)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicatePackSlugError(payload.slug) from exc
    version = TemplatePackVersion(
        pack_id=pack.id,
        version=1,
        status="draft",
        rules=payload.rules,
        source="user_authored",
        published_at=None,
    )
    session.add(version)
    await record_audit_event(
        session,
        event_type="template_pack.created",
        actor_user_id=user_id,
        details={"pack_id": str(pack.id), "slug": pack.slug, "version": 1},
    )
    await session.commit()
    await session.refresh(version)
    return ManagedTemplatePackResponse(
        id=pack.id,
        slug=pack.slug,
        name=pack.name,
        kind=pack.kind,
        versions=[_version_response(version)],
    )


async def create_pack_version(
    session: AsyncSession,
    *,
    pack_id: UUID,
    payload: TemplatePackVersionCreate,
    user_id: UUID,
) -> TemplatePackVersionResponse:
    pack = await session.get(TemplatePack, pack_id)
    if pack is None:
        raise LookupError(pack_id)
    source_rules: dict[str, Any] = {}
    if payload.source_version_id:
        source = await session.get(TemplatePackVersion, payload.source_version_id)
        if source is None or source.pack_id != pack_id:
            raise PackManagementError("Source version does not belong to this pack")
        source_rules = source.rules
    if payload.rules is None and not payload.source_version_id:
        raise PackManagementError("Rules or source_version_id is required")
    latest = await session.scalar(
        select(func.max(TemplatePackVersion.version)).where(TemplatePackVersion.pack_id == pack_id)
    )
    version = TemplatePackVersion(
        pack_id=pack_id,
        version=(latest or 0) + 1,
        status="draft",
        rules=payload.rules if payload.rules is not None else source_rules,
        source="user_authored",
        published_at=None,
    )
    session.add(version)
    await record_audit_event(
        session,
        event_type="template_pack.version_created",
        actor_user_id=user_id,
        details={"pack_id": str(pack_id), "version": version.version},
    )
    await session.commit()
    await session.refresh(version)
    return _version_response(version)


async def publish_pack_version(
    session: AsyncSession, *, version_id: UUID, user_id: UUID
) -> TemplatePackVersionResponse:
    version = await session.get(TemplatePackVersion, version_id)
    if version is None:
        raise LookupError(version_id)
    if version.status != "draft":
        raise PackManagementError("Only draft versions can be published")
    version.status = "published"
    version.published_at = datetime.now(UTC)
    await record_audit_event(
        session,
        event_type="template_pack.version_published",
        actor_user_id=user_id,
        details={"pack_id": str(version.pack_id), "version": version.version},
    )
    await session.commit()
    return _version_response(version)


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
