from collections.abc import AsyncIterator
from io import BytesIO

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from aiimage.api.dependencies import get_session
from aiimage.api.main import create_app
from aiimage.assets.models import Asset  # noqa: F401
from aiimage.assets.storage import InMemoryObjectStore, get_object_store
from aiimage.audit.models import AuditEvent  # noqa: F401
from aiimage.auth.models import Role, User  # noqa: F401
from aiimage.auth.service import create_access_token, create_user
from aiimage.catalog.models import Product, ProductReference, TruthAnchor  # noqa: F401
from aiimage.config import get_settings
from aiimage.db import Base
from aiimage.models.models import ModelConfiguration  # noqa: F401
from aiimage.quality.models import QualityCheck, QualityRun  # noqa: F401
from aiimage.review.models import ReviewDecision  # noqa: F401
from aiimage.templates.models import (  # noqa: F401
    ProductionPlan,
    ProductionPlanItem,
    TemplatePack,
    TemplatePackVersion,
)
from aiimage.workflow.models import GenerationBatch, GenerationStep  # noqa: F401


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def authenticated_app(session_factory):
    async with session_factory() as session:
        await create_user(
            session,
            email="admin@aiimage.local",
            password="LocalOnly-ChangeMe-2026",
            roles={Role.ADMIN},
        )
        await session.commit()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    return app


@pytest_asyncio.fixture
async def operator_client(session_factory) -> AsyncIterator[AsyncClient]:
    async with session_factory() as session:
        operator = await create_user(
            session,
            email="operator@aiimage.local",
            password="Operator-Password-2026",
            roles={Role.OPERATOR},
        )
        await session.commit()
        token = create_access_token(operator, secret=get_settings().jwt_secret)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client


@pytest_asyncio.fixture
async def admin_client(session_factory) -> AsyncIterator[AsyncClient]:
    async with session_factory() as session:
        admin = await create_user(
            session,
            email="admin@aiimage.local",
            password="LocalOnly-ChangeMe-2026",
            roles={Role.ADMIN},
        )
        await session.commit()
        token = create_access_token(admin, secret=get_settings().jwt_secret)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_object_store] = InMemoryObjectStore
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client


@pytest_asyncio.fixture
async def png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color="white").save(buffer, format="PNG")
    return buffer.getvalue()
