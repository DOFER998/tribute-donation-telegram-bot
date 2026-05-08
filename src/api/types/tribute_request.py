from datetime import datetime
from typing import Any

from ..enums import TributeRequestType
from .base import BaseObject


class TributeRequest(BaseObject):
    name: TributeRequestType
    created_at: datetime
    sent_at: datetime
    payload: dict[str, Any]
