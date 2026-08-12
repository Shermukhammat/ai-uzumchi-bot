from aiogram import types, F
from aiogram.fsm.context import FSMContext
from db.models import User
from buttons import Keyboards
from states import AdminPanel

from .. import r

@r.message(AdminPanel.main, F.text == "⚙️ Sozlamalar")
async def settings_menu(message: types.Message, state: FSMContext, user: User, session):
    await state.set_state(AdminPanel.settings)
    await message.answer("⚙️ Sozlamalar menyusiga xush kelibsiz", reply_markup=Keyboards.settings())

@r.message(AdminPanel.settings, F.text == "⬅️ Orqaga")
async def go_back_to_main(message: types.Message, state: FSMContext, user: User, session):
    await state.set_state(AdminPanel.main)
    await message.answer("👨🏻‍💻 Admin panelga qaytdingiz", reply_markup=Keyboards.admin_panel())

@r.message(AdminPanel.settings, F.text.not_in({"📡 Kanallar", "👨🏻‍💻 Adminlar"}))
async def settings_placeholders(message: types.Message, state: FSMContext, user: User, session):
    await message.answer(f"Nomalumt buyruq", reply_markup=Keyboards.settings())
