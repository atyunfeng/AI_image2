import uvicorn
from fastapi import APIRouter, FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="AI Image Platform", version="0.1.0")
    router = APIRouter(prefix="/api/v1")

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("aiimage.api.main:app", host="0.0.0.0", port=8000, reload=False)

