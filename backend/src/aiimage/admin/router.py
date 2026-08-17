from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.admin.schemas import (
    AdminUserCreate,
    AdminUserResponse,
    AdminUserUpdate,
    AuditEventPage,
)
from aiimage.admin.service import AdminConflictError, list_audit_events, list_users, update_user
from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import AdminUser
from aiimage.auth.models import User
from aiimage.auth.service import create_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserResponse])
async def read_users(
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[User]:
    del user
    return await list_users(session)


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_managed_user(
    payload: AdminUserCreate,
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    try:
        created = await create_user(
            session,
            email=payload.email,
            password=payload.password,
            roles=payload.roles,
            actor_user_id=user.id,
        )
        await session.commit()
        await session.refresh(created)
        return created
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail="User email already exists") from error


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_managed_user(
    user_id: UUID,
    payload: AdminUserUpdate,
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    target = await session.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return await update_user(
            session,
            target=target,
            actor_user_id=user.id,
            roles=payload.roles,
            is_active=payload.is_active,
            password=payload.password,
        )
    except AdminConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/audit", response_model=AuditEventPage)
async def read_audit_events(
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    event_type: Annotated[str | None, Query(max_length=100)] = None,
    actor_user_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AuditEventPage:
    del user
    return await list_audit_events(
        session,
        event_type=event_type,
        actor_user_id=actor_user_id,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=limit,
    )
