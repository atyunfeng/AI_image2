from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.models.schemas import ModelCreate, ModelResponse
from aiimage.models.service import create_model_configuration, to_response

router = APIRouter(prefix="/models", tags=["models"])
AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model_endpoint(
    payload: ModelCreate,
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ModelResponse:
    configuration = await create_model_configuration(session, payload=payload, user=user)
    return to_response(configuration)

