from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.templates.schemas import TemplatePackResponse
from aiimage.templates.service import list_published_packs

router = APIRouter(prefix="/template-packs", tags=["template-packs"])
TemplateUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.OPERATOR, Role.DESIGNER))
]


@router.get("", response_model=list[TemplatePackResponse])
async def list_template_packs(
    user: TemplateUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[TemplatePackResponse]:
    del user
    return await list_published_packs(session)
