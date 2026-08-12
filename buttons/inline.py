from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder



class InlineKeyboards:
    
    @staticmethod
    def ads_button_builder(buttons: list[dict]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for i, button in enumerate(buttons):
            text = button['text']
            color = button.get('color')
            if color:
                builder.row(InlineKeyboardButton(text=text, callback_data=f"button_{i}", style=color))
            else:
                builder.row(InlineKeyboardButton(text=text, callback_data=f"button_{i}"))
        
        builder.row(
            InlineKeyboardButton(text="➖", callback_data="remove_button"),
            InlineKeyboardButton(text="➕", callback_data="add_button")
        )
        return builder.as_markup()

    @staticmethod
    def ads_button(buttons: list[dict]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for i, button in enumerate(buttons):
            text = button['text']
            color = button.get('color')
            if color:
                builder.row(InlineKeyboardButton(text=text, url=button['url'], style=color))
            else:
                builder.row(InlineKeyboardButton(text=text, url=button['url']))
        
        return builder.as_markup()

    @staticmethod
    def color_selection() -> InlineKeyboardMarkup:
        colors = [
            ("Ko'k", "primary"), 
            ("Yashil", "success"), 
            ("Qizil", "danger"),
            ("Standart", "default")
        ]
        keyboard = []
        for text, val in colors:
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"color:{val}", style=val)])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def admins_panel() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Qo'shish", callback_data="admin_add"),
                InlineKeyboardButton(text="➖ O'chirish", callback_data="admin_remove")
            ]
        ])

    @staticmethod
    def channels_panel() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Qo'shish", callback_data="channel_add"),
                InlineKeyboardButton(text="➖ O'chirish", callback_data="channel_remove")
            ]
        ])

    @staticmethod
    def channel_config(request_join: bool) -> InlineKeyboardMarkup:
        zayavka_text = "✅ Zayavka" if request_join else "❌ Zayavka"
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Nomi", callback_data="config_title"),
                InlineKeyboardButton(text="✏️ Havola", callback_data="config_url")
            ],
            [
                InlineKeyboardButton(text=zayavka_text, callback_data="config_zayavka")
            ],
            [
                InlineKeyboardButton(text="✅ Tayyor", callback_data="config_done"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="config_cancel")
            ]
        ])

    @staticmethod
    def subscribe_channels(channels: list) -> InlineKeyboardMarkup:
        keyboard = []
        for ch in channels:
            keyboard.append([InlineKeyboardButton(text=ch.title, url=ch.url)])
        keyboard.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


InlineButtons = InlineKeyboards