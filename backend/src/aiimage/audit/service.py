from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.audit.models import AuditEvent


async def record_audit_event(
    session: AsyncSession,
    *,
    event_type: str,
    actor_user_id: UUID | None,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        event_type=event_type,
        details=details or {},
    )
    session.add(event)
    return event

