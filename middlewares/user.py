from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession
from db import DataBase
from db.models.user import User
from loader import bot


async def register_user(session: AsyncSession, tg_user: TelegramUser, db: DataBase) -> User:
    """
    Create and persist a new User row, then send a welcome message.

    Intentionally kept simple — easy to expand later:
      - Set an FSM state for a multi-step registration form.
      - Send a richer onboarding message or show a reply keyboard.
      - Grant default roles / permissions.
    """
    user = await db.users.create(
        session,
        id=tg_user.id,
        first_name=tg_user.first_name,
        username=tg_user.username,
        last_name=tg_user.last_name,
    )
    await bot.send_message(
        tg_user.id,
        f"👋 Welcome, {tg_user.first_name}! You have been registered.",
    )


class UserMiddleware(BaseMiddleware):
    """
    Injects a `User` ORM instance into every update that has a sender.

    Relies on DbSessionMiddleware having already set data["session"].

    Flow per update:
      1. Extract event_from_user — skip gracefully if absent (e.g. channel posts).
      2. Use the shared session to look up the user in DB.
      3. Auto-register + greet if not found.
      4. Inject as data["user"] and call the handler.

    Like DbSessionMiddleware, user injection is unconditional (no lazy
    signature inspection) because at the dp.update middleware level
    data["handler"].callback is aiogram's internal handler, not the
    user-defined one.
    """

    def __init__(self, db: DataBase) -> None:
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TelegramUser | None = data.get("event_from_user")

        if tg_user is not None:
            session: AsyncSession = data["session"]
            user = await self.db.users.get(session, tg_user.id)
            if user is None:
                return await register_user(session, tg_user, self.db)
            data["user"] = user

        return await handler(event, data)
