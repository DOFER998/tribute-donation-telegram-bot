from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class FundraiserAction(StrEnum):
    START_CREATE = 'start_create'
    CONFIRM_CREATE = 'confirm_create'
    CANCEL_CREATE = 'cancel_create'
    CLOSE_REQUEST = 'close_request'
    CLOSE_CONFIRM = 'close_confirm'
    BACK_TO_MENU = 'back'
    EXPORT_CSV = 'export_csv'


class FundraiserCreateCallback(CallbackData, prefix='fc'):
    action: FundraiserAction
