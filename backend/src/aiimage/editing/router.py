import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.assets.storage import ObjectStore, get_object_store
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.editing.evidence import latest_edit_evidence
from aiimage.editing.models import EditProject
from aiimage.editing.schemas import (
    CreateEditProjectRequest,
    EditEvidenceResponse,
    EditProjectResponse,
    EditRevisionResponse,
)
from aiimage.editing.service import (
    EditValidationError,
    create_ai_revision,
    create_composed_revision,
    create_edit_project,
    project_response,
)
from aiimage.workflow.queue import QueueHints, get_queue_hints

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


@router.post("/{project_id}/revisions/ai", response_model=EditRevisionResponse, status_code=201)
async def create_ai_revision_endpoint(
    project_id: UUID,
    user: EditUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[QueueHints, Depends(get_queue_hints)],
    store: Annotated[ObjectStore, Depends(get_object_store)],
    parent_revision_id: Annotated[UUID, Form()],
    operation: Annotated[str, Form()],
    prompt: Annotated[str, Form()],
    model_configuration_id: Annotated[UUID, Form()],
    parameters_json: Annotated[str, Form()] = "{}",
    mask: Annotated[UploadFile | None, File()] = None,
) -> EditRevisionResponse:
    try:
        parameters = json.loads(parameters_json)
        revision = await create_ai_revision(
            session,
            queue,
            store,
            project_id=project_id,
            parent_revision_id=parent_revision_id,
            operation=operation,
            prompt=prompt,
            model_configuration_id=model_configuration_id,
            parameters=parameters,
            mask_content=await mask.read() if mask else None,
            user_id=user.id,
        )
    except (EditValidationError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    response = await project_response(session, await session.get(EditProject, project_id))
    return next(item for item in response.revisions if item.id == revision.id)


@router.post("/{project_id}/revisions/compose", response_model=EditRevisionResponse, status_code=201)
async def create_composed_revision_endpoint(
    project_id: UUID,
    user: EditUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[ObjectStore, Depends(get_object_store)],
    parent_revision_id: Annotated[UUID, Form()],
    parameters_json: Annotated[str, Form()] = "{}",
    logo: Annotated[UploadFile | None, File()] = None,
) -> EditRevisionResponse:
    try:
        parameters = json.loads(parameters_json)
        revision = await create_composed_revision(
            session,
            store,
            project_id=project_id,
            parent_revision_id=parent_revision_id,
            parameters=parameters,
            logo_content=await logo.read() if logo else None,
            user_id=user.id,
        )
    except (EditValidationError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    response = await project_response(session, await session.get(EditProject, project_id))
    return next(item for item in response.revisions if item.id == revision.id)


@router.get("/revisions/{revision_id}/evidence", response_model=EditEvidenceResponse)
async def get_edit_evidence_endpoint(
    revision_id: UUID,
    user: EditUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EditEvidenceResponse:
    del user
    evidence = await latest_edit_evidence(session, revision_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Edit evidence not found")
    return EditEvidenceResponse.model_validate(evidence, from_attributes=True)


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
