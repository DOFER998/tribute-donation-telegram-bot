import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from granian import Granian
from granian.constants import Interfaces
from loguru import logger
from redis.asyncio import Redis

from src.__meta__ import __app_name__, __version__
from src.api.routers import telegram, tribute
from src.common import (
    BOT_PRIVATE_COMMANDS,
    env,
    setup_logging,
)
from src.middlewares import ThrottlingMiddleware
from src.routers import include_routers
from src.services import (
    CommandService,
    NotificationQueueService,
    SchedulerService,
    get_admin_commands,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    bot = Bot(
        token=env.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    redis = Redis.from_url(env.redis.dsn)
    storage = RedisStorage(redis, key_builder=DefaultKeyBuilder(with_destiny=True))
    dispatcher = Dispatcher(storage=storage, bot=bot, redis=redis)

    throttling = ThrottlingMiddleware()
    dispatcher.message.outer_middleware(throttling)
    dispatcher.callback_query.outer_middleware(throttling)

    include_routers(dispatcher)

    app.state.bot = bot
    app.state.redis = redis
    app.state.dispatcher = dispatcher

    cmd_service = CommandService(bot)
    await cmd_service.set_commands_all_private_chats(BOT_PRIVATE_COMMANDS)
    await cmd_service.set_commands_for_admins(
        admin_ids=env.admin.admin_ids,
        commands=[*BOT_PRIVATE_COMMANDS, *get_admin_commands()],
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(
        url=env.app.webhook_url,
        secret_token=env.app.secret_token.get_secret_value(),
        allowed_updates=dispatcher.resolve_used_update_types(),
        drop_pending_updates=True,
    )
    info = await bot.get_webhook_info()
    logger.info(
        'Webhook set: url={}, pending={}, last_error={}, allowed={}',
        info.url,
        info.pending_update_count,
        info.last_error_message or 'none',
        info.allowed_updates,
    )

    notification_queue = NotificationQueueService(bot, redis)
    app.state.notification_queue = notification_queue
    worker_task = asyncio.create_task(notification_queue.run_worker())

    scheduler_service = SchedulerService(bot, redis)
    await scheduler_service.start()

    logger.info('{} v{} started', __app_name__, __version__)

    try:
        yield
    finally:
        worker_task.cancel()
        await asyncio.gather(worker_task, return_exceptions=True)
        scheduler_service.stop()
        await cmd_service.delete_commands_all_private_chats()
        await cmd_service.delete_commands_for_admins(env.admin.admin_ids)
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.fsm.storage.close()
        await redis.aclose()
        await bot.session.close()
        logger.info('Bot shutdown')


setup_logging(debug=env.app.debug)

app = FastAPI(lifespan=lifespan)
app.include_router(telegram.router)
app.include_router(tribute.router)


@app.get('/')
async def healthcheck() -> dict[str, str]:
    return {'status': 'ok', 'app': __app_name__, 'version': __version__}


def main() -> None:
    command.upgrade(Config('alembic.ini'), 'head')

    server = Granian(
        target='src.main:app',
        address=env.app.host,
        port=env.app.port,
        interface=Interfaces.ASGI,
    )
    server.serve()


if __name__ == '__main__':
    main()
