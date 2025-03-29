from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_cancel_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Отметить 🙅‍♂️", callback_data="cancel-event")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
