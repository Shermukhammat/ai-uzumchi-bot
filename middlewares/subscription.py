import asyncio
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiocache import Cache
from sqlalchemy.ext.asyncio import AsyncSession
from db import DataBase
from loader import bot
from buttons import InlineButtons

sub_cache = Cache(Cache.MEMORY, ttl=60)

class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self, db: DataBase) -> None:
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        tg_user: TelegramUser | None = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)


        is_all_subbed = await sub_cache.get(tg_user.id)
        if is_all_subbed:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        channels = await self.db.channels.get_all(session)
        not_joined_channels = []

        for channel in channels:
            cache_key = f"sub_{tg_user.id}_{channel.id}"
            is_subbed = await sub_cache.get(cache_key)
            if is_subbed:
                continue

            try:
                member = await bot.get_chat_member(chat_id=channel.id, user_id=tg_user.id)
                if member.status in ['left', 'kicked', 'banned']:
                    not_joined_channels.append(channel)
            except (TelegramBadRequest, TelegramForbiddenError):
                await self.db.channels.delete(session, channel.id)
            except Exception:
                not_joined_channels.append(channel)

        if not not_joined_channels:
            await sub_cache.set(tg_user.id, True)
            return await handler(event, data)

        if isinstance(event, CallbackQuery) and event.data == "check_sub":
            await event.answer("Barcha kanallarga obuna bo'lishingiz kerak!", show_alert=True)
            return

        markup = InlineButtons.subscribe_channels(not_joined_channels)
        text = "Botimizdan foydalanish uchun quyidagi kanallarga obuna bo'ling 👇"
        
        if isinstance(event, Message):
            await event.answer(text, reply_markup=markup)
        elif isinstance(event, CallbackQuery):
            if event.data != "check_sub":
                await event.message.answer(text, reply_markup=markup)
                await event.answer()
