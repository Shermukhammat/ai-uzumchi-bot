import asyncio
from datetime import datetime
from aiogram import Bot, types
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from loader import db
from db.models import User
from typing import List

SLEEP_TIME = 0.05

def seconds_to_uz_time(seconds: int) -> str:
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if days:
        parts.append(f"{days} kun")
    if hours:
        parts.append(f"{hours} soat")
    if minutes:
        parts.append(f"{minutes} minut")
    if seconds or not parts:
        parts.append(f"{seconds} soniya")

    return " ".join(parts) or "0 soniya"


async def send_message_to_user(data: dict, user_id: int, bot: Bot, reply_markup=None, user: User=None) -> types.Message:
    msg_type = data.get('type')
    text_content = data.get('text') or data.get('caption')
    
    if user and isinstance(text_content, str):
        text_content = text_content.replace("{ism}", user.first_name)
        if user.last_name:
            text_content = text_content.replace("{toliq_ism}", f"{user.first_name} {user.last_name}")
        else:
            text_content = text_content.replace("{toliq_ism}", user.first_name)

    file_id = data.get('file_id') or data.get('text')  # Compatibility with both old and new formats

    if msg_type == 'text':
        return await bot.send_message(chat_id=user_id, text=text_content, reply_markup=reply_markup)
    elif msg_type == 'video':
        return await bot.send_video(chat_id=user_id, video=file_id, caption=text_content, reply_markup=reply_markup)
    elif msg_type == 'photo':
        return await bot.send_photo(chat_id=user_id, photo=file_id, caption=text_content, reply_markup=reply_markup)
    elif msg_type == 'audio':
        return await bot.send_audio(chat_id=user_id, audio=file_id, caption=text_content, reply_markup=reply_markup)
    elif msg_type == 'voice':
        return await bot.send_voice(chat_id=user_id, voice=file_id, caption=text_content, reply_markup=reply_markup)
    elif msg_type == 'document':
        return await bot.send_document(chat_id=user_id, document=file_id, caption=text_content, reply_markup=reply_markup)
    elif msg_type == 'video_note':
        return await bot.send_video_note(chat_id=user_id, video_note=file_id, reply_markup=reply_markup)


async def broadcast(data: dict, bot: Bot, update: types.Message, users: List[User], session):
    sended, failed, blocked_detect = 0, 0, 0
    start = datetime.now()
    
    reply_markup = data.get('reply_markup')

    for user in users:
        if not user.is_active:
            continue

        try:
            await send_message_to_user(data, user.id, bot, reply_markup, user)
            sended += 1
            await asyncio.sleep(SLEEP_TIME)

        except TelegramRetryAfter as e:
            failed += 1
            await asyncio.sleep(e.retry_after)
            # retry once
            try:
                await send_message_to_user(data, user.id, bot, reply_markup, user)
                sended += 1
            except:
                pass

        except TelegramForbiddenError:
            blocked_detect += 1
            user.is_active = False
            await db.users.update(session, user)
        except Exception:
            failed += 1
            
    end = datetime.now()
    duration = end - start
    await bot.send_message(
        update.from_user.id, 
        f"🏁 Xabar yuborish yakunlandi \n\n"
        f"⏳ Vaqt: {seconds_to_uz_time(duration.total_seconds())} \n"
        f"✅ Yuborildi: {sended} \n"
        f"❌ Yuborib bo'lmadi: {failed} \n"
        f"🚶 Tark etgan aniqlandi: {blocked_detect}"
    )
