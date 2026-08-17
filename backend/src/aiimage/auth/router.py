from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.audit.service import record_audit_event
from aiimage.auth.dependencies import AdminUser, CurrentUser
from aiimage.auth.models import User
from aiimage.auth.schemas import LoginRequest, TokenResponse, UserResponse
from aiimage.auth.service import authenticate_user, create_access_token
from aiimage.config import Settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    user = await authenticate_user(
        session,
        email=str(payload.email),
        password=payload.password,
    )
    if user is None:
        await record_audit_event(
            session,
            event_type="auth.login_failed",
            actor_user_id=None,
            details={"email": str(payload.email).lower()},
        )
        await session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    await record_audit_event(
        session,
        event_type="auth.login_succeeded",
        actor_user_id=user.id,
    )
    await session.commit()
    return TokenResponse(access_token=create_access_token(user, secret=settings.jwt_secret))


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> User:
    return user


@router.get("/admin-check", response_model=UserResponse)
async def admin_check(user: AdminUser) -> User:
    return user
