from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.common import env
from src.database import FundraiserRepository, async_session
from src.filters import IsAlertGroup
from src.keyboards import get_donate_keyboard
from src.services.fundraiser import render_progress_message

router = Router()
router.message.filter(IsAlertGroup())


@router.message(Command('stats'))
async def cmd_stats(message: Message) -> None:
    async with async_session() as session:
        f = await FundraiserRepository(session).get_active()

    if not f:
        await message.reply('Активных сборов нет.')
        return

    await message.reply(
        render_progress_message(f),
        reply_markup=get_donate_keyboard(env.tribute.donate_link),
    )
