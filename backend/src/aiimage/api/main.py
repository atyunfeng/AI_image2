import uvicorn
from fastapi import APIRouter, FastAPI

from aiimage.auth.router import router as auth_router
from aiimage.catalog.router import router as catalog_router


def create_app() -> FastAPI:
    app = FastAPI(title="AI Image Platform", version="0.1.0")
    router = APIRouter(prefix="/api/v1")

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(catalog_router, prefix="/api/v1")
    return app


app = create_app()


def run() -> None:
    uvicorn.run("aiimage.api.main:app", host="0.0.0.0", port=8000, reload=False)
