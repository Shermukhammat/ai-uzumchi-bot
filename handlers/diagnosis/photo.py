from aiogram import types, F
from . import r


PHOTO_RECEIVED_TEXT = (
    "Rasmingiz qabul qilindi ✅\n\n"
    "Tez orada tahlil natijasi bilan qaytaman."
)


@r.message(F.photo)
async def photo_handler(message: types.Message):
    await message.answer(PHOTO_RECEIVED_TEXT)
