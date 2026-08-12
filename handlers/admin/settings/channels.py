import re
from html import escape

from aiogram import types, F, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from .. import r
from states import AdminPanel
from buttons import Keyboards, InlineButtons
from db.models.channel import Channel
from loader import db
from config import MAX_CHANNELS

USER_NAME_AT = re.compile(r'^@?(?!.*__)[a-zA-Z][a-zA-Z0-9_]{3,30}[a-zA-Z0-9]$')
INVITE_LINK = re.compile(r'^(https?://)?t\.me/\S+$')


def _channels_text(channels: list[Channel]) -> str:
    if not channels:
        return "📡 Kanallar ro'yxati bo'sh"
    lines = ["📡 <b>Majburiy obuna kanallar:</b>\n"]
    for ch in channels:
        title = escape(ch.title)
        lines.append(f"• <code>{ch.id}</code> - <a href=\"{ch.url}\">{title}</a>")
    return "\n".join(lines)


def _normalize_invite_link(text: str) -> str | None:
    text = text.strip()
    if not INVITE_LINK.match(text):
        return None
    if text.startswith("http://") or text.startswith("https://"):
        return text
    return f"https://{text}"


async def _send_config_panel(message: types.Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title", "")
    url = data.get("url", "")
    request_join = data.get("request_join", False)
    
    zayavka_str = "✅ Yoqilgan" if request_join else "❌ O'chirilgan"
    text = (
        "⚙️ <b>Kanal sozlamalari:</b>\n\n"
        f"<b>Nomi:</b> {escape(title)}\n"
        f"<b>Havola:</b> {escape(url)}\n"
        f"<b>Zayavka:</b> {zayavka_str}"
    )
    msg = await message.answer("⏳", reply_markup=Keyboards.remove())
    await msg.delete()
    await message.answer(text, reply_markup=InlineButtons.channel_config(request_join=request_join), parse_mode="HTML")


@r.message(AdminPanel.settings, F.text == "📡 Kanallar")
async def show_channels(update: types.Message, session: AsyncSession):
    channels = await db.channels.get_all(session)
    await update.answer(_channels_text(channels), reply_markup=InlineButtons.channels_panel(), parse_mode="HTML")


@r.callback_query(AdminPanel.settings, F.data == "channel_add")
async def start_add_channel(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    channels = await db.channels.get_all(session)
    if len(channels) >= MAX_CHANNELS:
        await call.answer(f"❗️ {MAX_CHANNELS} tadan ko'p kanal qo'shish mumkin emas", show_alert=True)
        return
    await state.set_state(AdminPanel.add_channel)
    await call.message.delete()
    await call.message.answer(
        "Qo'shmoqchi bo'lgan kanal yoki guruhingizni tanlang:",
        reply_markup=Keyboards.request_channel()
    )
    await call.answer()


@r.message(AdminPanel.add_channel, F.text == "❌ Bekor qilish")
async def cancel_add_channel(update: types.Message, state: FSMContext, session: AsyncSession):
    await state.set_state(AdminPanel.settings)
    await update.answer("Kanal qo'shish bekor qilindi", reply_markup=Keyboards.settings())


@r.message(AdminPanel.add_channel, F.chat_shared)
async def process_chat_shared(message: types.Message, state: FSMContext, session: AsyncSession, bot: Bot):
    chat_id = message.chat_shared.chat_id
    
    existing = await db.channels.get(session, chat_id)
    if existing:
        await message.answer("ℹ️ Bu kanal allaqachon qo'shilgan")
        return

    try:
        # Check if bot is admin
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        if bot_member.status not in ("administrator", "creator"):
            await message.answer("❗️ Bot bu kanal/guruhda admin emas. Avval botni admin qiling")
            return
    except Exception:
        await message.answer("❗️ Bot bu kanal/guruhga kira olmaydi yoki admin emas. Avval botni admin qiling")
        return

    # Try to get chat title from telegram
    try:
        chat_info = await bot.get_chat(chat_id)
        title = chat_info.title or "Bizning kanal"
    except Exception:
        title = "Bizning kanal"

    try:
        invite_link = await bot.create_chat_invite_link(chat_id)
        url = invite_link.invite_link
    except Exception as e:
        await message.answer(f"❗️ Taklif havolasini yaratishda xatolik. Botda 'Invite Users' ruxsati borligini tekshiring.")
        return

    await state.update_data(channel_id=chat_id, title=title, url=url, request_join=False)
    await state.set_state(AdminPanel.channel_config)
    await _send_config_panel(message, state)


@r.message(AdminPanel.channel_config)
async def cancel_config_on_any_message(message: types.Message, state: FSMContext):
    await state.set_state(AdminPanel.settings)
    await message.answer("Kanal qo'shish bekor qilindi", reply_markup=Keyboards.settings())


@r.message(AdminPanel.add_channel, F.text, ~F.text.in_({"❌ Bekor qilish"}))
async def add_channel_text_fallback(message: types.Message):
    await message.answer("Iltimos, quyidagi tugmalar orqali kanal yoki guruhni tanlang:", reply_markup=Keyboards.request_channel())


@r.callback_query(AdminPanel.channel_config, F.data == "config_title")
async def config_edit_title(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminPanel.edit_channel_title)
    await call.message.delete()
    await call.message.answer("Yangi nomni kiriting (Maksimum 60 ta belgi):", reply_markup=Keyboards.back())
    await call.answer()


@r.message(AdminPanel.edit_channel_title, F.text == "⬅️ Orqaga")
async def back_to_config_from_title(message: types.Message, state: FSMContext):
    await state.set_state(AdminPanel.channel_config)
    await _send_config_panel(message, state)


@r.message(AdminPanel.edit_channel_title, F.text)
async def process_new_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    if len(title) > 60:
        await message.answer("❗️ Nom juda uzun. Iltimos qisqaroq nom kiriting:", reply_markup=Keyboards.back())
        return
    
    await state.update_data(title=title)
    await state.set_state(AdminPanel.channel_config)
    await _send_config_panel(message, state)


@r.callback_query(AdminPanel.channel_config, F.data == "config_url")
async def config_edit_url(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminPanel.edit_channel_url)
    await call.message.delete()
    await call.message.answer("Yangi havolani kiriting (https://t.me/...):", reply_markup=Keyboards.back())
    await call.answer()


@r.message(AdminPanel.edit_channel_url, F.text == "⬅️ Orqaga")
async def back_to_config_from_url(message: types.Message, state: FSMContext):
    await state.set_state(AdminPanel.channel_config)
    await _send_config_panel(message, state)


@r.message(AdminPanel.edit_channel_url, F.text)
async def process_new_url(message: types.Message, state: FSMContext):
    url = _normalize_invite_link(message.text)
    if not url:
        await message.answer("❗️ Noto'g'ri havola. Iltimos https://t.me/... formatida kiriting:", reply_markup=Keyboards.back())
        return
    
    await state.update_data(url=url)
    await state.set_state(AdminPanel.channel_config)
    await _send_config_panel(message, state)


@r.callback_query(AdminPanel.channel_config, F.data == "config_zayavka")
async def config_toggle_zayavka(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    new_request_join = not data.get("request_join", False)
    await state.update_data(request_join=new_request_join)
    
    title = data.get("title", "")
    url = data.get("url", "")
    
    zayavka_str = "✅ Yoqilgan" if new_request_join else "❌ O'chirilgan"
    text = (
        "⚙️ <b>Kanal sozlamalari:</b>\n\n"
        f"<b>Nomi:</b> {escape(title)}\n"
        f"<b>Havola:</b> {escape(url)}\n"
        f"<b>Zayavka:</b> {zayavka_str}"
    )
    await call.message.edit_text(text, reply_markup=InlineButtons.channel_config(request_join=new_request_join), parse_mode="HTML")
    await call.answer()


@r.callback_query(AdminPanel.channel_config, F.data == "config_done")
async def config_done(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    title = data.get("title", "Kanal")
    url = data.get("url")
    request_join = data.get("request_join", False)
    
    await db.channels.add(session, id=channel_id, title=title, url=url, request_join=request_join)
    
    await state.set_state(AdminPanel.settings)
    await call.message.delete()
    await call.message.answer(
        f"✅ <b>{escape(title)}</b> kanali muvaffaqiyatli qo'shildi!",
        reply_markup=Keyboards.settings(),
        parse_mode="HTML"
    )
    await call.answer()


@r.callback_query(AdminPanel.channel_config, F.data == "config_cancel")
async def config_cancel(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(AdminPanel.settings)
    await call.message.delete()
    await call.message.answer("Kanal qo'shish bekor qilindi", reply_markup=Keyboards.settings())
    await call.answer()


@r.callback_query(AdminPanel.settings, F.data == "channel_remove")
async def start_remove_channel(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminPanel.remove_channel)
    await call.message.edit_reply_markup()
    await call.message.answer(
        "✍️ O'chirmoqchi bo'lgan kanalning ID sini yuboring",
        reply_markup=Keyboards.cancel()
    )
    await call.answer()


@r.message(AdminPanel.remove_channel, F.text == "❌ Bekor qilish")
async def cancel_remove_channel(update: types.Message, state: FSMContext, session: AsyncSession):
    await state.set_state(AdminPanel.settings)
    await update.answer("Kanalni o'chirish bekor qilindi", reply_markup=Keyboards.settings())


@r.message(AdminPanel.remove_channel, F.text)
async def remove_channel(update: types.Message, state: FSMContext, session: AsyncSession):
    if not update.text.lstrip("-").isdigit():
        await update.answer("❗️ Iltimos, to'g'ri ID yuboring")
        return

    channel_id = int(update.text)
    deleted = await db.channels.delete(session, channel_id)
    if not deleted:
        await update.answer("❗️ Bunday kanal topilmadi:")
        return

    await state.set_state(AdminPanel.settings)
    await update.answer("✅ Kanal o'chirildi", reply_markup=Keyboards.settings())
