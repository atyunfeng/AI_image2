from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore, get_object_store
from aiimage.auth.dependencies import get_current_user
from aiimage.auth.models import User

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/{asset_id}/content")
async def asset_content(
    asset_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[ObjectStore, Depends(get_object_store)],
    if_none_match: Annotated[str | None, Header()] = None,
) -> Response:
    del user
    asset = await session.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    etag = f'"{asset.sha256}"'
    if if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})
    return Response(
        content=await store.get(object_key=asset.object_key),
        media_type=asset.mime_type,
        headers={"ETag": etag, "Cache-Control": "private, max-age=31536000, immutable"},
    )
