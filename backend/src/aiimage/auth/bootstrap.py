import asyncio

from aiimage.auth.models import Role
from aiimage.auth.service import create_user, get_user_by_email
from aiimage.config import get_settings
from aiimage.db import get_database


async def bootstrap_admin() -> None:
    settings = get_settings()
    database = get_database()
    async with database.session_factory() as session:
        if await get_user_by_email(session, settings.bootstrap_admin_email) is None:
            await create_user(
                session,
                email=settings.bootstrap_admin_email,
                password=settings.bootstrap_admin_password,
                roles={Role.ADMIN, Role.OPERATOR, Role.REVIEWER},
            )
            await session.commit()
    await database.dispose()


def main() -> None:
    asyncio.run(bootstrap_admin())


if __name__ == "__main__":
    main()
