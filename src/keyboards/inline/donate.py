from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_donate_keyboard(donate_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='💳 Поддержать', url=donate_link)],
        ],
    )
