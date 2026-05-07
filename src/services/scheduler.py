from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from redis.asyncio import Redis

from src.common import MOSCOW_TZ, env

from .digest import DigestService
from .fundraiser import FundraiserService


async def _check_expired(bot: Bot) -> None:
    await FundraiserService(bot).check_and_close_expired()


async def _send_digest(bot: Bot) -> None:
    await DigestService(bot).send_daily()


class SchedulerService:
    def __init__(self, bot: Bot, redis: Redis) -> None:
        self.bot = bot
        self.redis = redis
        self.scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)

    async def start(self) -> None:
        self.scheduler.add_job(
            _check_expired,
            'interval',
            minutes=30,
            id='check_expired',
            replace_existing=True,
            args=[self.bot],
        )
        self.scheduler.add_job(
            _send_digest,
            'cron',
            hour=env.digest.hour,
            minute=0,
            id='daily_digest',
            replace_existing=True,
            args=[self.bot],
        )
        self.scheduler.start()
        logger.info('Scheduler started: digest at {}:00 MSK', env.digest.hour)

    def stop(self) -> None:
        self.scheduler.shutdown()
