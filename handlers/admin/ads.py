from aiogram import types, F, Bot
from aiogram.filters import Command
from db.models import User
from loader import db
from buttons import Keyboards, InlineKeyboards
from states import AdminPanel, AdsSending
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import phone_router, broadcast, send_message_to_user, seconds_to_uz_time
import re
import asyncio

from . import r

url_pattern = r"^https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)$"
brodcast_sema = asyncio.Semaphore()

@r.message(AdminPanel.main, F.text == "📢 Xabar yuborish")
async def enter_ads_menu(update: types.Message, state: FSMContext):
    await state.set_state(AdsSending.get_message)
    await state.update_data(buttons=[])
    await update.answer(
        "↪️ Xabaringizni yuboring (matn, rasm, video...)\n"
        "PS: Foydalanuvchi ismini qo'shish uchun {ism} yoki {toliq_ism} yozing",
        reply_markup=Keyboards.cancel()
    )

@r.message(AdsSending.get_message, F.text == "❌ Bekor qilish")
async def cancel_ads(update: types.Message, state: FSMContext):
    await state.set_state(AdminPanel.main)
    await update.answer("❌ Bekor qilindi", reply_markup=Keyboards.admin_panel())

@r.message(AdsSending.get_message, F.text | F.video | F.photo | F.audio | F.voice | F.document | F.video_note)
async def get_message(update: types.Message, state: FSMContext, bot: Bot, user: User, session):
    if update.text:
        await state.update_data(text=update.text, caption=None, type='text')
    elif update.video:
        await state.update_data(file_id=update.video.file_id, caption=update.caption, type='video')
    elif update.photo:
        await state.update_data(file_id=update.photo[-1].file_id, caption=update.caption, type='photo')
    elif update.audio:
        await state.update_data(file_id=update.audio.file_id, caption=update.caption, type='audio')
    elif update.voice:
        await state.update_data(file_id=update.voice.file_id, caption=update.caption, type='voice')
    elif update.document:
        await state.update_data(file_id=update.document.file_id, caption=update.caption, type='document')
    elif update.video_note:
        await state.update_data(file_id=update.video_note.file_id, caption=None, type='video_note')

    await state.set_state(AdsSending.get_buttons)
    state_data = await state.get_data()
    buttons = state_data.get('buttons', [])
    
    await send_message_to_user(state_data, update.chat.id, bot, reply_markup=InlineKeyboards.ads_button_builder(buttons), user=user)
    
    await update.reply(
        "👌 Yaxshi endi xabarga tugma qo'shishingiz mumkin\n"
        "yoki o'tkazish uchun ➡️ Keyingi tugmasini bosing",
        reply_markup=Keyboards.back(next=True)
    )

@r.callback_query(AdsSending.get_buttons, F.data == "add_button")
async def start_adding_button(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdsSending.get_button_name)
    await call.message.answer("Tugma nomini kiriting:", reply_markup=Keyboards.back())
    await call.answer()

@r.message(AdsSending.get_button_name, F.text)
async def get_button_name(message: types.Message, state: FSMContext, bot: Bot, user: User, session):
    if message.text == "⬅️ Orqaga":
        await state.set_state(AdsSending.get_buttons)
        data = await state.get_data()
        buttons = data.get('buttons', [])
        await send_message_to_user(data, message.chat.id, bot, reply_markup=InlineKeyboards.ads_button_builder(buttons), user=user)
        return await message.answer("Tugma qo'shish bekor qilindi.", reply_markup=Keyboards.back(next=True))
        
    await state.update_data(temp_button_name=message.text)
    await state.set_state(AdsSending.get_button_url)
    await message.answer("Tugma manzilini (URL) yoki telefon raqamini (masalan: +998901234567) kiriting:", reply_markup=Keyboards.back())

@r.message(AdsSending.get_button_url, F.text)
async def get_button_url(message: types.Message, state: FSMContext, bot: Bot, user: User, session):
    if message.text == "⬅️ Orqaga":
        await state.set_state(AdsSending.get_button_name)
        return await message.answer("Tugma nomini kiriting:", reply_markup=Keyboards.back())

    url = message.text.strip()
    
    # Oddiy telefon raqamini tekshirish (faqat raqamlar yoki + belgisi)
    if any(char.isdigit() for char in url) and not url.startswith("http"):
        url = phone_router(url)
    elif not re.match(url_pattern, url):
        return await message.answer("❗️ Xavola noto'g'ri. Iltimos to'g'ri URL yoki telefon raqam kiriting:", reply_markup=Keyboards.back())
        
    await state.update_data(temp_button_url=url)
    await state.set_state(AdsSending.get_button_color)
    await message.answer("Tugma rangini tanlang (yoki standartni qoldiring):", reply_markup=InlineKeyboards.color_selection())

@r.message(AdsSending.get_button_color, F.text == "⬅️ Orqaga")
async def back_from_button_color(message: types.Message, state: FSMContext):
    await state.set_state(AdsSending.get_button_url)
    await message.answer("Tugma manzilini (URL) yoki telefon raqamini (masalan: +998901234567) kiriting:", reply_markup=Keyboards.back())

@r.callback_query(AdsSending.get_button_color, F.data.startswith("color:"))
async def get_button_color(call: types.CallbackQuery, state: FSMContext, bot: Bot, user: User, session):
    color = call.data.split(":")[1]
    data = await state.get_data()

    new_button = {
        'text': data.get('temp_button_name'),
        'url': data.get('temp_button_url'),
        'color': color
    }
    
    buttons = data.get('buttons', [])
    buttons.append(new_button)
    await state.update_data(buttons=buttons)
    
    await state.set_state(AdsSending.get_buttons)
    await call.message.delete()
    
    await send_message_to_user(data, call.from_user.id, bot, reply_markup=InlineKeyboards.ads_button_builder(buttons), user=user)
    await call.message.answer(
        "Tugma qo'shildi. Yana qo'shishingiz mumkin yoki ➡️ Keyingi ni bosing.",
        reply_markup=Keyboards.back(next=True)
    )
    await call.answer()

@r.callback_query(AdsSending.get_buttons, F.data == "remove_button")
async def remove_button_menu(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    buttons = data.get('buttons', [])
    
    if not buttons:
        return await call.answer("O'chirish uchun tugmalar yo'q!", show_alert=True)
        
    await state.set_state(AdsSending.get_remove_button)
    
    keyboard = []
    for i, b in enumerate(buttons):
        keyboard.append([InlineKeyboardButton(text=f"❌ {b['text']}", callback_data=f"del_btn:{i}")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="del_btn:back")])
    
    await call.message.answer("O'chirmoqchi bo'lgan tugmani tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await call.answer()

@r.callback_query(AdsSending.get_remove_button, F.data.startswith("del_btn:"))
async def remove_button_action(call: types.CallbackQuery, state: FSMContext, bot: Bot, user: User, session):
    action = call.data.split(":")[1]
    
    if action == "back":
        await state.set_state(AdsSending.get_buttons)
        await call.message.delete()
        return await call.answer()
        
    idx = int(action)
    data = await state.get_data()
    buttons = data.get('buttons', [])
    
    if 0 <= idx < len(buttons):
        buttons.pop(idx)
        await state.update_data(buttons=buttons)
        
    await state.set_state(AdsSending.get_buttons)
    await call.message.delete()
    await send_message_to_user(data, call.from_user.id, bot, reply_markup=InlineKeyboards.ads_button_builder(buttons), user=user)
    await call.message.answer("Tugma o'chirildi.", reply_markup=Keyboards.back(next=True))
    await call.answer()

@r.message(AdsSending.get_buttons, F.text == "⬅️ Orqaga")
async def go_back(update: types.Message, state: FSMContext):
    await state.set_state(AdsSending.get_message)
    await update.answer("Xabaringizni yuboring:", reply_markup=Keyboards.cancel())

@r.message(AdsSending.get_buttons, F.text == "➡️ Keyingi")
async def next_ads(update: types.Message, state: FSMContext, bot: Bot, user: User, session):
    await state.set_state(AdsSending.confirm)
    state_data = await state.get_data()
    buttons = state_data.get('buttons', [])
    
    reply_markup = InlineKeyboards.ads_button(buttons) if buttons else None
    
    await send_message_to_user(state_data, update.from_user.id, bot, reply_markup=reply_markup, user=user)
    await update.answer("Yuborishni tasdiqlaysizmi? Boshlash uchun '🚀 Yuborish' tugmasini bosing.", reply_markup=Keyboards.confirm_send())

@r.message(AdsSending.confirm, F.text)
async def confirm_send(update: types.Message, state: FSMContext, bot: Bot, user: User, session):
    if update.text == "⬅️ Orqaga":
        await state.set_state(AdsSending.get_buttons)
        data = await state.get_data()
        buttons = data.get('buttons', [])
        await send_message_to_user(data, update.chat.id, bot, reply_markup=InlineKeyboards.ads_button_builder(buttons), user=user)
        return await update.reply("Tugmani qo'shish yoki o'chirish menyusi", reply_markup=Keyboards.back(next=True))
    elif update.text == "❌ Bekor qilish":
        await state.set_state(AdminPanel.main)
        await update.answer("❌ Xabar yuborish bekor qilindi", reply_markup=Keyboards.admin_panel())
        
    elif update.text == "🚀 Yuborish":
        state_data = await state.get_data()
        buttons = state_data.get('buttons', [])
        
        if buttons:
            state_data['reply_markup'] = InlineKeyboards.ads_button(buttons)
        else:
            state_data['reply_markup'] = None

        await state.set_state(AdminPanel.main)
        
        users = await db.users.get_all(session)
        active_users_count = len([u for u in users if u.is_active])
        estimeted_time = 0.05 * active_users_count
        est_time = seconds_to_uz_time(estimeted_time)

        await update.answer(f"🔄 Xabar yuborish boshlandi ... \n⏳ Taxminy yuborish vaxti: {est_time}", reply_markup=Keyboards.admin_panel())

        async with brodcast_sema:
            # We call the broadcast logic as background task or simply await it
            await broadcast(state_data, bot, update, users, session)
        
    else:
        await update.reply("Noma'lum buyruq. Yuborish uchun '🚀 Yuborish' tugmasini bosing.")
