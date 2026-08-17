import uvicorn
from fastapi import APIRouter, FastAPI

from aiimage.assets.router import router as asset_router
from aiimage.auth.router import router as auth_router
from aiimage.catalog.router import router as catalog_router
from aiimage.editing.router import router as editing_router
from aiimage.export.router import router as export_router
from aiimage.fashion.router import router as fashion_router
from aiimage.models.router import router as model_router
from aiimage.quality.router import router as quality_router
from aiimage.review.router import router as review_router
from aiimage.talent.router import router as talent_router
from aiimage.templates.router import plan_router
from aiimage.templates.router import router as template_router
from aiimage.workflow.router import router as workflow_router


def create_app() -> FastAPI:
    app = FastAPI(title="AI Image Platform", version="0.1.0")
    router = APIRouter(prefix="/api/v1")

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(asset_router, prefix="/api/v1")
    app.include_router(catalog_router, prefix="/api/v1")
    app.include_router(editing_router, prefix="/api/v1")
    app.include_router(model_router, prefix="/api/v1")
    app.include_router(template_router, prefix="/api/v1")
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
