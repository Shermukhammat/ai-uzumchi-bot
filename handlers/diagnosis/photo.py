import asyncio

from aiogram import types, F

from loader import bot
from ml.classifier import HEALTHY_LABEL, PredictionResult, predict
from . import r


PROCESSING_EMOJI = "🔍"

# Below this the model's top guess isn't reliable enough to show as a diagnosis.
CONFIDENCE_THRESHOLD = 0.4

NOT_DETECTED_TEXT = (
    "🤔 <b>Aniqlay olmadim</b>\n\n"
    "Rasmda tok bargini yetarlicha aniq tanib bo'lmadi. Iltimos:\n"
    "• bargni yaqindan va yaxshi yorug'likda suratga oling;\n"
    "• bitta barg butun rasmga sig'sin;\n"
    "• rasm xira yoki qorong'i bo'lmasin.\n\n"
    "So'ng rasmni qayta yuboring 📸"
)


def build_result_text(result: PredictionResult) -> str:
    if result.label == HEALTHY_LABEL:
        return (
            "✅ <b>Barg sog'lom</b>\n"
            "Kasallik alomatlari aniqlanmadi.\n\n"
            f"📊 Ishonch darajasi: <b>{result.confidence:.0%}</b>"
        )

    return (
        "⚠️ <b>Kasallik aniqlandi</b>\n"
        f"🦠 Tashxis: <b>{result.label_uz}</b>\n\n"
        f"📊 Ishonch darajasi: <b>{result.confidence:.0%}</b>"
    )


@r.message(F.photo)
async def photo_handler(message: types.Message):
    processing_message = await message.answer(PROCESSING_EMOJI)

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    buffer = await bot.download_file(file.file_path)
    image_bytes = buffer.read()

    result = await asyncio.to_thread(predict, image_bytes)

    await processing_message.delete()

    if result.confidence < CONFIDENCE_THRESHOLD:
        await message.answer(NOT_DETECTED_TEXT, parse_mode="HTML")
        return

    await message.answer(build_result_text(result), parse_mode="HTML")
