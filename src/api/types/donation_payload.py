from typing import Optional

from pydantic import Field

from .base import BaseObject


class DonationPayload(BaseObject):
    donation_request_id: int
    donation_name: str
    message: Optional[str] = None
    period: str = ''
    amount: int
    currency: str
    anonymously: bool = False
    web_app_link: str = ''
    email: Optional[str] = None
    trb_user_id: Optional[str] = None
    user_id: Optional[int] = Field(default=None, deprecated=True)
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
