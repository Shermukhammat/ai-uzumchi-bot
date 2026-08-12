from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession
from db import DataBase
from db.models.user import User
from loader import bot
from utils.messages import build_welcome_text


def _is_start_command(event: TelegramObject) -> bool:
    message = getattr(event, "message", None)
    text = getattr(message, "text", None) if message else None
    return bool(text) and text.split()[0] == "/start"


async def register_user(session: AsyncSession, tg_user: TelegramUser, db: DataBase, event: TelegramObject) -> User:
    """
    Create and persist a new User row, then greet them.

    The /start command is the one case where we skip the greeting here —
    its own handler sends the identical welcome text right after, and we
    don't want it twice. For every other kind of first contact (random
    text, a photo, ...) this is the only place the welcome message gets
    sent, since the triggering handler won't know the user is brand new.
    """
    user = await db.users.create(
        session,
        id=tg_user.id,
        first_name=tg_user.first_name,
        username=tg_user.username,
        last_name=tg_user.last_name,
    )
    if not _is_start_command(event):
        await bot.send_message(tg_user.id, build_welcome_text(tg_user.first_name, db.bot.full_name))
    return user


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
            data["is_new_user"] = user is None
            if user is None:
                user = await register_user(session, tg_user, self.db, event)
            data["user"] = user

        return await handler(event, data)
