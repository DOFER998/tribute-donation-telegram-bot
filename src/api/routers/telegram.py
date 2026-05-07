from typing import Annotated

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Depends, Request, Response
from loguru import logger

from src.common import BOT_WEBHOOK_PATH

from ..dependencies import get_bot, get_dispatcher, verify_telegram_secret

router = APIRouter()


@router.post(BOT_WEBHOOK_PATH, dependencies=[Depends(verify_telegram_secret)])
async def telegram_webhook(
    request: Request,
    bot: Annotated[Bot, Depends(get_bot)],
    dispatcher: Annotated[Dispatcher, Depends(get_dispatcher)],
) -> Response:
    data = await request.json()
    try:
        update = Update.model_validate(data, context={'bot': bot})
        await dispatcher.feed_update(bot, update)
    except Exception:  # noqa: BLE001
        logger.exception('Failed to feed update')
    return Response(content='OK')
