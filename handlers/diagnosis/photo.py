import asyncio

from aiogram import types, F
from google.genai import errors as genai_errors

from db.models import User
from loader import bot
from ml.classifier import HEALTHY_LABEL, PredictionResult, predict
from utils.llm import generate_diagnosis_info, text_to_speech
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

INFO_UNAVAILABLE_TEXT = (
    "⚠️ Qo'shimcha ma'lumot olishda xatolik yuz berdi. "
    "Birozdan so'ng qayta urinib ko'ring."
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
async def photo_handler(message: types.Message, user: User):
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

    await bot.send_chat_action(
        message.chat.id,
        "record_voice" if user.voice_replies_enabled else "typing",
    )
    try:
        info_text = await generate_diagnosis_info(result)
    except genai_errors.APIError:
        await message.answer(INFO_UNAVAILABLE_TEXT)
        return

    if not user.voice_replies_enabled:
        await message.answer(info_text)
        return

    try:
        voice_bytes = await text_to_speech(info_text)
        await message.answer_voice(types.BufferedInputFile(voice_bytes, filename="diagnosis.ogg"))
    except genai_errors.APIError:
        await message.answer(info_text)
