from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_court_select_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Hard", callback_data="court-type:hard")],
        [InlineKeyboardButton(text="I.Hard", callback_data="court-type:i.hard")],
        [InlineKeyboardButton(text="Clay", callback_data="court-type:clay")],
        [InlineKeyboardButton(text="Capret", callback_data="court-type:capret")],
        [InlineKeyboardButton(text="Grass", callback_data="court-type:grass")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
