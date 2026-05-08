from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class FundraiserAction(StrEnum):
    CONFIRM = 'confirm'
    CANCEL = 'cancel'


class FundraiserCreateCallback(CallbackData, prefix='fc'):
    action: FundraiserAction
