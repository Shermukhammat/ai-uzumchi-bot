from aiogram import types, F
from aiogram.enums import ContentType
from . import r


FALLBACK_TEXT = (
    "Men buni tushunmadim 🙂\n\n"
    "Tahlil qilishim uchun menga tok bargining bitta aniq rasmini yuboring — "
    "boshlash uchun shu bitta rasm kifoya 📸"
)


@r.message(F.content_type == ContentType.TEXT, ~F.text.startswith("/"))
async def fallback_handler(message: types.Message, is_new_user: bool):
    if is_new_user:
        return
    await message.answer(FALLBACK_TEXT)
