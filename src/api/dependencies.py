from typing import Annotated

from aiogram import Bot, Dispatcher
from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from src.common import env
from src.services import DonationService, FundraiserService, NotificationQueueService

from .utils import verify_tribute_signature as _verify


def get_bot(request: Request) -> Bot:
    return request.app.state.bot


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_dispatcher(request: Request) -> Dispatcher:
    return request.app.state.dispatcher


async def verify_telegram_secret(request: Request) -> None:
    secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
    if secret != env.app.secret_token.get_secret_value():
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid secret token')


async def verify_tribute_body(request: Request) -> bytes:
    body = await request.body()
    if not body:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Empty body')

    sig = request.headers.get('trbt-signature')
    if not _verify(body, sig, env.tribute.api_key.get_secret_value()):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid signature')

    return body


def get_donation_service(bot: Annotated[Bot, Depends(get_bot)]) -> DonationService:
    return DonationService(bot)


def get_notification_queue(request: Request) -> NotificationQueueService:
    return request.app.state.notification_queue


def get_fundraiser_service(bot: Annotated[Bot, Depends(get_bot)]) -> FundraiserService:
    return FundraiserService(bot)
