from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from db import DataBase


class DbSessionMiddleware(BaseMiddleware):
    """
    Opens an AsyncSession for every update and injects it as data["session"].

    The session is always created (no lazy inspection) because at the
    dp.update middleware level data["handler"].callback is aiogram's internal
    routing handler — not the user-defined handler — so signature inspection
    cannot reliably detect whether the eventual handler needs a session.

    The session is kept open for the entire handler call and closed (connection
    returned to the asyncpg pool) once the handler returns, even on error.
    """

    def __init__(self, db: DataBase) -> None:
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.db.session_maker() as session:
            data["session"] = session
            return await handler(event, data)