from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.db import Database, get_database


async def get_session(
    database: Database = Depends(get_database),
) -> AsyncIterator[AsyncSession]:
    async for session in database.session():
        yield session

