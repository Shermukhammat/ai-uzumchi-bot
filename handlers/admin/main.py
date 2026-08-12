from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from db.models import User
from loader import db
from buttons import Keyboards
from states import AdminPanel
from . import r



@r.message(Command('admin'))
async def show_admin_panel(update: types.Message, session, user: User, state: FSMContext):
    if not user.is_admin:
        return
    
    await state.set_state(AdminPanel.main)
    await update.answer("👨🏻‍💻 Admin panel", reply_markup=Keyboards.admin_panel())


@r.message(AdminPanel.main, F.text == "⬅️ Chiqish")
async def go_back(update: types.Message, session, user: User, state: FSMContext):
    await state.clear()
    await update.answer("👋 Admin paneldan chiqdingiz", reply_markup=Keyboards.remove())
