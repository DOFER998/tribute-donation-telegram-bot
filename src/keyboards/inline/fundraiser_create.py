from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.callback_data import FundraiserAction, FundraiserCreateCallback


def _btn(text: str, action: FundraiserAction) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=FundraiserCreateCallback(action=action).pack(),
    )


def get_empty_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[_btn('➕ Создать сбор', FundraiserAction.START_CREATE)]]
    )


def get_active_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn('📊 Выгрузка CSV', FundraiserAction.EXPORT_CSV)],
            [_btn('⏹ Закрыть сбор', FundraiserAction.CLOSE_REQUEST)],
        ]
    )


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[_btn('✖️ Отмена', FundraiserAction.CANCEL_CREATE)]]
    )


def get_topic_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn('📭 Без топика (общий чат)', FundraiserAction.SKIP_TOPIC)],
            [_btn('✖️ Отмена', FundraiserAction.CANCEL_CREATE)],
        ]
    )


def get_confirm_create_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn('✅ Запустить сбор', FundraiserAction.CONFIRM_CREATE),
                _btn('✖️ Отмена', FundraiserAction.CANCEL_CREATE),
            ]
        ]
    )


def get_close_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn('✅ Да, закрыть', FundraiserAction.CLOSE_CONFIRM),
                _btn('✖️ Назад', FundraiserAction.BACK_TO_MENU),
            ]
        ]
    )
