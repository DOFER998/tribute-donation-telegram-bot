import asyncio
import json
from json import JSONDecodeError

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from loguru import logger
from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.api.types import DonationPayload
from src.common import (
    NOTIFICATION_QUEUE_KEY,
    env,
    get_user_display_name,
    render,
)
from src.keyboards import get_donate_keyboard


class NotificationQueueService:
    def __init__(self, bot: Bot, redis: Redis) -> None:
        self.bot = bot
        self.redis = redis

    async def push(self, payload: DonationPayload, is_anonymous: bool) -> None:
        data = json.dumps(
            {
                'payload': payload.model_dump(mode='json'),
                'is_anonymous': is_anonymous,
            }
        )
        await self.redis.rpush(NOTIFICATION_QUEUE_KEY, data)
        logger.debug('Queued alert: amount={}', payload.amount)

    async def run_worker(self) -> None:
        logger.info('Notification worker started')
        while True:
            try:
                result = await self.redis.blpop(NOTIFICATION_QUEUE_KEY, timeout=0)
                if result:
                    _, raw = result
                    await self._process_one(raw)
            except asyncio.CancelledError:
                logger.info('Notification worker stopped')
                return
            except (RedisError, JSONDecodeError, ValidationError, TelegramAPIError, OSError):
                logger.exception('Notification worker error')

    async def _process_one(self, raw: bytes) -> None:
        msg = json.loads(raw)
        payload = DonationPayload.model_validate(msg['payload'])
        is_anonymous: bool = msg.get('is_anonymous', False)

        if is_anonymous or not payload.telegram_user_id:
            display_name = 'Аноним'
        else:
            username, full_name = await get_user_display_name(
                self.bot, env.tribute.alert_group_id, payload.telegram_user_id
            )
            display_name = full_name or (f'@{username}' if username else 'Аноним')

        text = await render(
            'donation_alert.html.j2',
            display_name=display_name,
            amount_kopecks=payload.amount,
            comment=payload.message,
        )

        markup = get_donate_keyboard(env.tribute.donate_link)

        for attempt in range(3):
            try:
                await self.bot.send_message(
                    chat_id=env.tribute.alert_group_id,
                    message_thread_id=env.tribute.alert_topic_id,
                    text=text,
                    reply_markup=markup,
                )
            except TelegramRetryAfter as e:
                if attempt == 2:
                    raise
                logger.warning('Flood control, retry in {}s', e.retry_after)
                await asyncio.sleep(e.retry_after)
            else:
                logger.info('Donation alert sent')
                return
