from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.admin.schemas import AuditEventPage, AuditEventResponse
from aiimage.audit.models import AuditEvent
from aiimage.audit.service import record_audit_event
from aiimage.auth.models import Role, User
from aiimage.auth.service import hash_password


class AdminConflictError(RuntimeError):
    pass


def _redact(value: Any, key: str = "") -> Any:
    if any(marker in key.lower() for marker in ("password", "secret", "token", "api_key")):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(child_key): _redact(child_value, str(child_key)) for child_key, child_value in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


async def list_users(session: AsyncSession) -> list[User]:
    return list((await session.scalars(select(User).order_by(User.created_at, User.email))).all())


async def update_user(
    session: AsyncSession,
    *,
    target: User,
    actor_user_id: UUID,
    roles: set[Role] | None,
    is_active: bool | None,
    password: str | None,
) -> User:
    next_roles = sorted(role.value for role in roles) if roles is not None else target.roles
    next_active = target.is_active if is_active is None else is_active
    removes_active_admin = (
        target.is_active
        and Role.ADMIN.value in target.roles
        and (not next_active or Role.ADMIN.value not in next_roles)
    )
    if removes_active_admin:
        active_admins = [
            user
            for user in await list_users(session)
            if user.is_active and Role.ADMIN.value in user.roles
        ]
        if len(active_admins) <= 1:
            raise AdminConflictError("The final active administrator cannot be disabled")
    changed: list[str] = []
    if roles is not None and next_roles != target.roles:
        target.roles = next_roles
        changed.append("roles")
    if is_active is not None and is_active != target.is_active:
        target.is_active = is_active
        changed.append("is_active")
    if password is not None:
        target.password_hash = hash_password(password)
        changed.append("password")
    if changed:
        await record_audit_event(
            session,
            event_type="user.updated",
            actor_user_id=actor_user_id,
            details={"user_id": str(target.id), "changed_fields": changed},
        )
    await session.commit()
    await session.refresh(target)
    return target


async def list_audit_events(
    session: AsyncSession,
    *,
    event_type: str | None,
    actor_user_id: UUID | None,
    date_from: datetime | None,
    date_to: datetime | None,
    offset: int,
    limit: int,
) -> AuditEventPage:
    filters = []
    if event_type:
        filters.append(AuditEvent.event_type == event_type)
    if actor_user_id:
        filters.append(AuditEvent.actor_user_id == actor_user_id)
    if date_from:
        filters.append(AuditEvent.created_at >= date_from)
    if date_to:
        filters.append(AuditEvent.created_at <= date_to)
    total = int(
        await session.scalar(select(func.count(AuditEvent.id)).where(*filters)) or 0
    )
    events = list(
        (
            await session.scalars(
                select(AuditEvent)
                .where(*filters)
                .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
                .offset(offset)
                .limit(limit)
            )
        ).all()
    )
    return AuditEventPage(
        total=total,
        items=[
            AuditEventResponse(
                id=event.id,
                actor_user_id=event.actor_user_id,
                event_type=event.event_type,
                details=_redact(event.details),
                created_at=event.created_at,
            )
            for event in events
        ],
    )
