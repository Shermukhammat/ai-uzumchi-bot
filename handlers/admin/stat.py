from aiogram import types, F
from aiogram.filters import Command
from db.models import User
from loader import db
from . import r

@r.message(F.text == "📊 Statistika")
@r.message(Command('stats', 'stat'))
async def show_statistics(message: types.Message, session, user: User):
    if not user.is_admin:
        return

    stats = await db.stats.get_users_stat(session)
    
    text = (
        f"📊 <b> {db.bot.full_name} statistikasi</b>\n\n"
        f"👥 <b>Foydalanuvchilar:</b> {stats.total_users}\n"
        f"  ├ Faol: {stats.active_users}\n"
        f"  └ Nofaol: {stats.inactive_users}\n"
        f"📈 <b>Yangi foydalanuvchilar:</b>\n"
        f"  ├ Bugun: {stats.new_today}\n"
        f"  ├ Shu hafta: {stats.new_this_week}\n"
        f"  └ Shu oy: {stats.new_this_month}\n"
        f"🔥 <b>Faollik:</b>\n"
        f"  ├ Bugun: {stats.active_today}\n"
        f"  ├ Shu hafta: {stats.active_this_week}\n"
        f"  └ Shu oy: {stats.active_this_month}"
    )
    
    await message.answer(text, parse_mode="HTML")
