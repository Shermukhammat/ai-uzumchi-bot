import asyncio
from aiogram.types import ChatJoinRequest
from . import r
from loader import bot
from middlewares.subscription import sub_cache

async def approve_request_later(chat_id: int, user_id: int):
    # Wait for 3 seconds before approving
    await asyncio.sleep(3)
    try:
        await bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
    except Exception:
        pass

@r.chat_join_request()
async def chat_join_request_handler(event: ChatJoinRequest):
    # Immediately mark the user as joined in the cache so they can use the bot
    cache_key = f"sub_{event.from_user.id}_{event.chat.id}"
    await sub_cache.set(cache_key, True)
    
    # Auto-approve the request in the background
    asyncio.create_task(approve_request_later(event.chat.id, event.from_user.id))
