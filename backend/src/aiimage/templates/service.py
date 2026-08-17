from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.templates.models import TemplatePack, TemplatePackVersion
from aiimage.templates.presets import first_party_packs
from aiimage.templates.schemas import TemplatePackResponse


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
