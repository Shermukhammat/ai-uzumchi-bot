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
