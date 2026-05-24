from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_session


async def session_dependency() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


def settings_dependency() -> Settings:
    return get_settings()


SessionDep = Annotated[AsyncSession, Depends(session_dependency)]
SettingsDep = Annotated[Settings, Depends(settings_dependency)]
