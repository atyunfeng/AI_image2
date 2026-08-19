import uvicorn
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, FastAPI, Response, status
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from aiimage.admin.router import router as admin_router
from aiimage.analytics.router import router as analytics_router
from aiimage.assets.router import router as asset_router
from aiimage.assets.storage import get_object_store
from aiimage.auth.router import router as auth_router
from aiimage.bulk.router import router as bulk_router
from aiimage.catalog.router import router as catalog_router
from aiimage.config import get_settings
from aiimage.db import get_database
from aiimage.editing.router import router as editing_router
from aiimage.export.router import router as export_router
from aiimage.fashion.router import router as fashion_router
from aiimage.models.router import router as model_router
from aiimage.quality.router import router as quality_router
from aiimage.review.router import router as review_router
from aiimage.talent.router import router as talent_router
from aiimage.templates.router import plan_router
from aiimage.templates.router import router as template_router
from aiimage.templates.router import version_router as template_version_router
from aiimage.workflow.router import router as workflow_router


def create_app() -> FastAPI:
    app = FastAPI(title="AI Image Platform", version="0.1.0")
    router = APIRouter(prefix="/api/v1")

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/health/live")
    async def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/health/ready")
    async def readiness(response: Response) -> dict[str, object]:
        checks: dict[str, bool] = {
            "database": False,
            "redis": False,
            "object_store": False,
            "worker": False,
        }
        database = get_database()
        settings = get_settings()
        redis = Redis.from_url(settings.redis_url)
        try:
            async with database.session_factory() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = True
        except SQLAlchemyError:
            checks["database"] = False
        try:
            checks["redis"] = bool(await redis.ping())
            checks["worker"] = await redis.exists("aiimage:worker:heartbeat") == 1
        except RedisError:
            checks["redis"] = False
            checks["worker"] = False
        finally:
            await redis.aclose()
        try:
            await get_object_store().health()
            checks["object_store"] = True
        except (BotoCoreError, ClientError, OSError):
            checks["object_store"] = False
        ready = all(checks.values())
        if not ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "ready" if ready else "degraded", "checks": checks}

    app.include_router(router)
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")
    app.include_router(asset_router, prefix="/api/v1")
    app.include_router(bulk_router, prefix="/api/v1")
    app.include_router(catalog_router, prefix="/api/v1")
    app.include_router(editing_router, prefix="/api/v1")
    app.include_router(model_router, prefix="/api/v1")
    app.include_router(template_router, prefix="/api/v1")
    app.include_router(template_version_router, prefix="/api/v1")
    app.include_router(plan_router, prefix="/api/v1")
    app.include_router(talent_router, prefix="/api/v1")
    app.include_router(fashion_router, prefix="/api/v1")
    app.include_router(workflow_router, prefix="/api/v1")
    app.include_router(review_router, prefix="/api/v1")
    app.include_router(quality_router, prefix="/api/v1")
    app.include_router(export_router, prefix="/api/v1")
    return app


app = create_app()


def run() -> None:
    uvicorn.run("aiimage.api.main:app", host="0.0.0.0", port=8000, reload=False)
