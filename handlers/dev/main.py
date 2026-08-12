from aiogram import types, F, Bot
from aiogram.filters import Command
from db.models import User
from loader import db
import config
from utils.command import set_admin_commands
from . import r


@r.message(Command("dev"), F.from_user.id == config.DEV_ID)
async def start_handler(update: types.Message, session, user: User):
    await update.answer(
        f"👨🏻‍💻 Available developer commands:\n\n" 
        f"/dev - Show all developer commands\n" 
        f"/make_me_admin - Make developer admin\n" 
        f"/debug - Turn on/off debug mode\n"
        f"/delete_me - Delete user from db if debug mode enabled"
        )
    

@r.message(Command('debug'), F.from_user.id == config.DEV_ID)
async def debug_handler(update: types.Message):
    config.DEBUG = not config.DEBUG
    state = "enabled" if config.DEBUG else "disabled"
    await update.answer(f"Debug mode has been {state}.")


@r.message(Command('make_me_admin'), F.from_user.id == config.DEV_ID)
async def make_me_admin_handler(update: types.Message, bot: Bot, session, user: User):
    if user.is_admin:
        await update.answer("You are already an admin!")
        return
    
    user.is_admin = True
    await db.users.update(session, user)
    await set_admin_commands(update.from_user.id, bot)
    await update.answer("You are now an admin!")


@r.message(Command('delete_me'))
async def delete_me_handler(update: types.Message, session):
    if config.DEBUG:
        await db.users.delete(session, update.from_user.id)
        await update.answer("Your account has been deleted.")
    else:
        await update.answer("Debug mode is disabled. Cannot delete account.")
