from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from src.common import env


class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return bool(user and user.id in env.admin.admin_ids)
