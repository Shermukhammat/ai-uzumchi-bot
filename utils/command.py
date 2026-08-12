from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeAllPrivateChats


ADMIN_COMMANDS = [
    BotCommand(command='admin', description="👨🏻‍💻 Admin panel"),
    BotCommand(command='stats', description="📊 Bot statistikasi"),
    ]

async def set_admin_commands(user_id: int, bot: Bot):
    await bot.set_my_commands(ADMIN_COMMANDS,  scope=BotCommandScopeChat(chat_id=user_id))


USER_COMMANDS = [
    BotCommand(command='start', description="🍇 Botni qayta ishga tushirish"),
    BotCommand(command='ovoz', description="🔊 Ovozli xabar yuborishni yoqish/o'chirish"),
]

async def set_user_commands(user_id: int, bot: Bot):
    if USER_COMMANDS:
        await bot.set_my_commands(USER_COMMANDS,  scope=BotCommandScopeChat(chat_id=user_id))


async def set_default_commands(bot: Bot):
    await bot.set_my_commands(USER_COMMANDS, scope=BotCommandScopeAllPrivateChats())
