from aiogram import types, F, Bot
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from .. import r
from states import AdminPanel
from buttons import Keyboards, InlineButtons
from db.models import User
from loader import db
from utils.command import set_admin_commands


def _admins_text(admins: list[User]) -> str:
    if not admins:
        return "👨🏻‍💻 Adminlar ro'yxati bo'sh"
    lines = ["👨🏻‍💻 <b>Adminlar ro'yxati:</b>\n"]
    for a in admins:
        full_name = a.first_name + (f" {a.last_name}" if a.last_name else "")
        if a.username:
            username = a.username.lstrip('@')
            lines.append(f"• <code>{a.id}</code> - <a href='https://t.me/{username}'>{full_name}</a>")
        else:
            lines.append(f"• <code>{a.id}</code> - {full_name}")
    return "\n".join(lines)


@r.message(AdminPanel.settings, F.text == "👨🏻‍💻 Adminlar")
async def show_admins(update: types.Message, session: AsyncSession):
    admins = await db.users.get_admins(session)
    await update.answer(_admins_text(admins), reply_markup=InlineButtons.admins_panel(), parse_mode="HTML")


@r.callback_query(AdminPanel.settings, F.data == "admin_add")
async def start_add_admin(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminPanel.adding_admin)
    await call.message.delete()
    await call.message.answer("➕ Admin qilmoqchi bo'lgan foydalanuvchini tanlang:", reply_markup=Keyboards.request_user())
    await call.answer()


@r.callback_query(AdminPanel.settings, F.data == "admin_remove")
async def start_remove_admin(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminPanel.removing_admin)
    await call.message.answer("➖ O'chirmoqchi bo'lgan admin ID sini yuboring:", reply_markup=Keyboards.cancel())
    await call.answer()


@r.message(AdminPanel.adding_admin, F.text == "❌ Bekor qilish")
async def cancel_add_admin(update: types.Message, state: FSMContext, session: AsyncSession):
    await state.set_state(AdminPanel.settings)
    await update.answer("Admin qo'shish bekor qilindi", reply_markup=Keyboards.settings())


@r.message(AdminPanel.adding_admin, F.users_shared)
async def process_users_shared(message: types.Message, state: FSMContext, session: AsyncSession, user: User, bot: Bot):
    # Get the first user ID from the list (request_id 3)
    target_id = message.users_shared.user_ids[0]

    if target_id == user.id:
        await message.answer("❗️ O'zingizni admin qila olmaysiz")
        return

    target = await db.users.get(session, target_id)
    if target is None:
        await message.answer("❗️ Bu foydalanuvchi botdan foydalanmagan. Avval u botga /start bosishi kerak")
        return

    if target.is_admin:
        await message.answer("ℹ️ Bu foydalanuvchi allaqachon admin")
        return

    target.is_admin = True
    await db.users.update(session, target)
    await set_admin_commands(target_id, bot)
    
    try:
        await bot.send_message(target_id, "🎉 Siz admin etib tayinlandingiz!")
    except Exception:
        pass

    full_name = target.first_name + (f" {target.last_name}" if target.last_name else "")
    await state.set_state(AdminPanel.settings)
    await message.answer(
        f"✅ <code>{target_id}</code> — {full_name} admin qilindi",
        reply_markup=Keyboards.settings(),
        parse_mode="HTML"
    )


@r.message(AdminPanel.adding_admin, F.text, ~F.text.in_({"❌ Bekor qilish"}))
async def add_admin_fallback(message: types.Message):
    await message.answer("Iltimos, quyidagi tugma orqali foydalanuvchini tanlang:", reply_markup=Keyboards.request_user())


@r.message(AdminPanel.removing_admin, F.text == "❌ Bekor qilish")
async def cancel_remove_admin(update: types.Message, state: FSMContext, session: AsyncSession):
    await state.set_state(AdminPanel.settings)
    await update.answer("Admin o'chirish bekor qilindi", reply_markup=Keyboards.settings())


@r.message(AdminPanel.removing_admin, F.text)
async def remove_admin(update: types.Message, state: FSMContext, session: AsyncSession, user: User, bot: Bot):
    text = update.text.strip()
    if not text.lstrip("-").isdigit():
        await update.answer("❗️ Iltimos, to'g'ri ID yuboring:")
        return

    target_id = int(text)

    if target_id == user.id:
        await update.answer("❗️ O'zingizni adminlikdan olib tashlay olmaysiz:")
        return

    target = await db.users.get(session, target_id)
    if target is None:
        await update.answer("❗️ Bunday foydalanuvchi topilmadi:")
        return

    if not target.is_admin:
        await update.answer("ℹ️ Bu foydalanuvchi admin emas:")
        return

    target.is_admin = False
    await db.users.update(session, target)
    
    try:
        await bot.delete_my_commands(scope=types.BotCommandScopeChat(chat_id=target_id))
    except Exception:
        pass

    try:
        await bot.send_message(target_id, "ℹ️ Siz adminlar ro'yxatidan o'chirildingiz.")
    except Exception:
        pass

    full_name = target.first_name + (f" {target.last_name}" if target.last_name else "")
    await state.set_state(AdminPanel.settings)
    await update.answer(
        f"✅ <code>{target_id}</code> - {full_name} adminlikdan olindi",
        reply_markup=Keyboards.settings(),
        parse_mode="HTML"
    )
