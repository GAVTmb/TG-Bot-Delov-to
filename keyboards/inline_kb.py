from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_callback_buts(*, buts: dict[str, str], sizes: tuple[int] = (2, )):
    keyboard = InlineKeyboardBuilder()
    for text, data in buts.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))
    return keyboard.adjust(*sizes).as_markup(resize_keyboard=True)
