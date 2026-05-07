from typing import Final

from aiogram.types import BotCommand
from pytz import BaseTzInfo, timezone

BOT_WEBHOOK_PATH: Final[str] = '/telegram'
TRIBUTE_WEBHOOK_PATH: Final[str] = '/tribute'
TEST_TRIBUTE_WEBHOOK_RESPONSE: Final[dict[str, str]] = {'test_event': 'test_event'}

BOT_PRIVATE_COMMANDS: Final[list[BotCommand]] = [
    BotCommand(command='start', description='Главное меню'),
]

MOSCOW_TZ: Final[BaseTzInfo] = timezone('Europe/Moscow')

NOTIFICATION_QUEUE_KEY: Final[str] = 'tribute:notifications'

TELEGRAM_MESSAGE_MAX_LENGTH: Final[int] = 4096
