from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.audit.service import record_audit_event
from aiimage.auth.models import Role, User

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_access_token(user: User, *, secret: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "roles": user.roles,
        "iat": now,
        "exp": now + timedelta(hours=8),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, *, secret: str) -> tuple[UUID, set[Role]]:
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    return UUID(payload["sub"]), {Role(role) for role in payload["roles"]}


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    roles: set[Role],
    actor_user_id: UUID | None = None,
) -> User:
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        roles=sorted(role.value for role in roles),
    )
    session.add(user)
    await session.flush()
    await record_audit_event(
        session,
        event_type="user.created",
        actor_user_id=actor_user_id,
        details={"user_id": str(user.id), "roles": user.roles},
    )
    return user


async def authenticate_user(session: AsyncSession, *, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if user is None or not user.is_active or not verify_password(user.password_hash, password):
        return None
    return user

