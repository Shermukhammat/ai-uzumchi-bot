from aiogram import F
from aiogram.types import CallbackQuery
from . import r

@r.callback_query(F.data == "check_sub")
async def handle_check_sub(call: CallbackQuery):
    await call.message.delete()
    await call.answer("Endi botdan foydalanishingiz mumkin!", show_alert=True)
