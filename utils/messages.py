from ml.classifier import HEALTHY_LABEL, LABELS_UZ

WELCOME_TEXT = (
    "👋 Assalomu alaykum, {first_name}! {bot_name} botiga xush kelibsiz.\n\n"
    "Men tok bargi rasmi orqali quyidagilarni aniqlab beraman:\n"
    "🍃 Tok navini\n"
    "🩺 Bargda kasallik bor-yo'qligini va qaysi kasallik ekanini\n"
    "💊 Kasallikni qanday davolash kerakligini\n"
    "🌱 Parvarish, hosil yig'ish va boshqa foydali maslahatlarni\n\n"
    "Natijani olgach, savollaringizni matn yoki ovozli xabar orqali "
    "so'rashingiz mumkin.\n"
    "Ovozli javoblarni yoqish/o'chirish uchun /ovoz buyrug'idan foydalaning.\n\n"
    "Boshlash uchun menga tok bargining bitta aniq rasmini yuboring 📸"
)


def build_welcome_text(first_name: str, bot_name: str) -> str:
    return WELCOME_TEXT.format(first_name=first_name, bot_name=bot_name)


def _detectable_conditions_list() -> str:
    lines = [f"✅ {LABELS_UZ[HEALTHY_LABEL]}"]
    lines += [f"🦠 {label_uz}" for label, label_uz in LABELS_UZ.items() if label != HEALTHY_LABEL]
    return "\n".join(lines)


HELP_TEXT = (
    "🆘 <b>Yordam</b>\n\n"
    "Men tok bargi rasmidan quyidagi holatlarni aniqlay olaman:\n\n"
    f"{_detectable_conditions_list()}\n\n"
    "<b>Qanday ishlatiladi:</b>\n"
    "1️⃣ Tok bargining bitta, yaqindan va yaxshi yorug'likda tushirilgan "
    "rasmini yuboring.\n"
    "2️⃣ Men rasmni tahlil qilib, holatni va ishonch darajasini aniqlayman.\n"
    "3️⃣ Aniqlangan holat bo'yicha sababi, davolash usullari va tavsiyalarni "
    "yuboraman — matn yoki ovozli xabar sifatida.\n\n"
    "🔊 Ovozli javoblarni yoqish/o'chirish: /ovoz\n\n"
    "Boshlash uchun menga tok bargi rasmini yuboring 📸"
)
