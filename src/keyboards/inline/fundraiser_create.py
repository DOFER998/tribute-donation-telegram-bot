from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.callback_data import FundraiserAction, FundraiserCreateCallback


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✖️ Отмена',
                    callback_data=FundraiserCreateCallback(action=FundraiserAction.CANCEL).pack(),
                )
            ]
        ]
    )


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✅ Запустить сбор',
                    callback_data=FundraiserCreateCallback(action=FundraiserAction.CONFIRM).pack(),
                ),
                InlineKeyboardButton(
                    text='✖️ Отмена',
                    callback_data=FundraiserCreateCallback(action=FundraiserAction.CANCEL).pack(),
                ),
            ]
        ]
    )
