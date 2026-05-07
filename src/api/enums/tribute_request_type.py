from enum import StrEnum


class TributeRequestType(StrEnum):
    NEW_DONATION = 'new_donation'
    RECURRENT_DONATION = 'recurrent_donation'
    NEW_SUBSCRIPTION = 'new_subscription'
    CANCELLED_SUBSCRIPTION = 'cancelled_subscription'
