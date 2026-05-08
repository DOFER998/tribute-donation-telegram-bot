from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.common import render
from src.filters import IsPrivate

router = Router()
router.message.filter(IsPrivate())


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user_name = message.from_user.full_name if message.from_user else 'друг'
    await message.answer(await render('start.html.j2', user_name=user_name))
