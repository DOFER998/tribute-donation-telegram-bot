from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.common import env, render
from src.database import FundraiserRepository, async_session
from src.filters import IsPrivate
from src.keyboards import get_donate_keyboard

router = Router()
router.message.filter(IsPrivate())


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user_name = message.from_user.full_name if message.from_user else 'друг'

    async with async_session() as session:
        fundraiser = await FundraiserRepository(session).get_active()

    text = await render(
        'start.html.j2',
        user_name=user_name,
        fundraiser=fundraiser,
    )
    await message.answer(text, reply_markup=get_donate_keyboard(env.tribute.donate_link))
