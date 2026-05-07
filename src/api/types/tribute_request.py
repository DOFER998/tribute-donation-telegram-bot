from datetime import datetime

from ..enums import TributeRequestType
from .base import BaseObject
from .donation_payload import DonationPayload


class TributeRequest(BaseObject):
    name: TributeRequestType
    created_at: datetime
    sent_at: datetime
    payload: DonationPayload
