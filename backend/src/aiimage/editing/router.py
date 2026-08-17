from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.editing.models import EditProject
from aiimage.editing.schemas import CreateEditProjectRequest, EditProjectResponse
from aiimage.editing.service import (
    EditValidationError,
    create_edit_project,
    project_response,
)

router = APIRouter(prefix="/edit-projects", tags=["edit-projects"])
EditUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.OPERATOR, Role.DESIGNER))]


@router.post("", response_model=EditProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_endpoint(
    payload: CreateEditProjectRequest,
    user: EditUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EditProjectResponse:
    try:
        project = await create_edit_project(
            session,
            source_batch_id=payload.source_batch_id,
            name=payload.name,
            user_id=user.id,
        )
    except EditValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return await project_response(session, project)


@router.get("/{project_id}", response_model=EditProjectResponse)
async def get_project_endpoint(
    project_id: UUID,
    user: EditUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EditProjectResponse:
    del user
    project = await session.get(EditProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Edit project not found")
    return await project_response(session, project)
