import asyncio

from google import genai
from google.genai import errors, types

from config import GEMINI_API_KEY
from ml.classifier import HEALTHY_LABEL, PredictionResult

_client = genai.Client(api_key=GEMINI_API_KEY)

# "-latest" alias so this keeps working as Google deprecates pinned model
# versions out from under new API keys (gemini-2.5-flash 404'd this way).
TEXT_MODEL = "gemini-flash-latest"
TTS_MODEL = "gemini-3.1-flash-tts-preview"
TTS_VOICE = "Kore"

# PCM format Gemini's TTS models return (see ffmpeg args in text_to_speech).
_TTS_SAMPLE_RATE = 24000

# Gemini's "high demand" 503s are usually a few seconds of spike, not an
# outage — one retry clears most of them without making the user wait long.
_RETRY_DELAY_SECONDS = 3

_HEALTHY_PROMPT = """\
Siz tokchilik (uzumchilik) bo'yicha tajribali agronomsiz. Foydalanuvchi \
yuborgan tok bargi tahlil qilindi va sog'lom deb aniqlandi — kasallik \
alomatlari topilmadi.

Foydalanuvchiga sodda o'zbek tilida, tokzorni sog'lom saqlash bo'yicha \
3-4 ta qisqa va amaliy tavsiya bering (masalan: parvarish, sug'orish, \
profilaktika). Javobni oddiy matn ko'rinishida yozing — markdown yoki \
HTML teglarisiz, faqat oddiy jumlalar bilan.\
"""

_DISEASE_PROMPT = """\
Siz tokchilik (uzumchilik) bo'yicha tajribali agronomsiz. Foydalanuvchi \
yuborgan tok bargida "{disease}" kasalligi aniqlandi (aniqlik darajasi: \
{confidence:.0%}).

Foydalanuvchiga sodda va tushunarli o'zbek tilida quyidagilarni qisqa \
tarzda tushuntiring:
1. Bu kasallik nima va odatda nima sababdan paydo bo'ladi.
2. Uni qanday davolash mumkin — aniq, amaliy qadamlar.
3. Kelajakda oldini olish uchun tavsiyalar.

Javobni oddiy matn ko'rinishida yozing — markdown yoki HTML teglarisiz, \
5-7 ta qisqa jumladan iborat bo'lsin. Ishonchsiz yoki noaniq \
ma'lumotlarni to'qib chiqarmang.\
"""


def _build_prompt(result: PredictionResult) -> str:
    if result.label == HEALTHY_LABEL:
        return _HEALTHY_PROMPT

    return _DISEASE_PROMPT.format(disease=result.label_uz, confidence=result.confidence)


async def _generate_content_with_retry(**kwargs):
    try:
        return await _client.aio.models.generate_content(**kwargs)
    except errors.ServerError:
        await asyncio.sleep(_RETRY_DELAY_SECONDS)
        return await _client.aio.models.generate_content(**kwargs)


async def generate_diagnosis_info(result: PredictionResult) -> str:
    """Gemini-generated Uzbek text: cause/treatment/prevention (diseased)
    or general care tips (healthy), grounded in the classifier's output."""
    response = await _generate_content_with_retry(
        model=TEXT_MODEL,
        contents=_build_prompt(result),
    )
    return response.text.strip()


async def text_to_speech(text: str) -> bytes:
    """Renders text to an OGG/Opus clip (Telegram voice message format)
    via Gemini's TTS model, piping its raw PCM output through ffmpeg."""
    response = await _generate_content_with_retry(
        model=TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=TTS_VOICE)
                )
            ),
        ),
    )
    pcm_bytes = response.candidates[0].content.parts[0].inline_data.data
    return await _pcm_to_ogg(pcm_bytes)


async def _pcm_to_ogg(pcm_bytes: bytes) -> bytes:
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-f", "s16le", "-ar", str(_TTS_SAMPLE_RATE), "-ac", "1", "-i", "pipe:0",
        "-c:a", "libopus", "-f", "ogg", "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await process.communicate(pcm_bytes)
    return stdout
