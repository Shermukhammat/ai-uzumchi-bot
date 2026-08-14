from aiogram import types
from aiogram.filters import Command
from db.models import User
from db import DataBase
from utils.messages import build_welcome_text, HELP_TEXT
from . import r


@r.message(Command("start"))
async def start_handler(message: types.Message, session, user: User, db: DataBase):
    await message.answer(build_welcome_text(user.first_name, db.bot.full_name))


@r.message(Command("ovoz"))
async def toggle_voice_handler(message: types.Message, session, user: User, db: DataBase):
    user.voice_replies_enabled = not user.voice_replies_enabled
    await db.users.update(session, user)

    status = "yoqilgan ✅" if user.voice_replies_enabled else "o'chirilgan ❌"
    await message.answer(f"🔊 Ovozli xabar yuborish {status}")


@r.message(Command("yordam"))
async def help_handler(message: types.Message):
    await message.answer(HELP_TEXT, parse_mode="HTML")
