from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_skip_rating_writing():
    keyboard = [[InlineKeyboardButton(text="Пропустить ⏭️", callback_data="skip-rating-writing")]]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
