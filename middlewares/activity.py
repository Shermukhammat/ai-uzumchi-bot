from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiocache import Cache

from loader import db

TTL = 60  # seconds
_cache = Cache(Cache.MEMORY, ttl=TTL)


class ActivityMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if tg_user is None:
            return await handler(event, data)

        cached = await _cache.get(tg_user.id)
        if not cached:
            session = data.get("session")
            if session:
                await db.users.update_last_used(session, tg_user.id)

            await _cache.set(tg_user.id, True)

        return await handler(event, data)
