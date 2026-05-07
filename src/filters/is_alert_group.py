from aiogram.filters import Filter
from aiogram.types import Message

from src.common import env


class IsAlertGroup(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.id == env.tribute.alert_group_id
