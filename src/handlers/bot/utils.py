from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Функция для создания стартовой клавиатуры
def create_start_kb(show_admin_buttons: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Спросить", callback_data="ask")],
            [
                InlineKeyboardButton(
                    text="Настройки",
                    callback_data="settings",
                )
            ],
        ]
    )
    # Добавляем кнопку для административной панели если show_admin_buttons равно True
    if show_admin_buttons:
        kb.inline_keyboard.append([InlineKeyboardButton(text="Административная панель", callback_data="admin_panel")])
    return kb
