import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    """Один запрос в 0.5 сек на пользователя."""

    def __init__(self, rate: float = 0.5) -> None:
        self.rate = rate
        self._last: dict[int, float] = {}
        self._lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id
            async with self._lock:
                now = time.monotonic()
                last = self._last.get(user_id, 0)
                if now - last < self.rate:
                    return None
                self._last[user_id] = now
        return await handler(event, data)
