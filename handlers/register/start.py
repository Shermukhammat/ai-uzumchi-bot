from aiogram import types
from aiogram.filters import Command
from db.models import User
from db import DataBase
from . import r


@r.message(Command("start"))
async def start_handler(message: types.Message, session, user: User, db: DataBase):
    await message.answer(f"{db.bot.full_name} ga xush kelibsiz")