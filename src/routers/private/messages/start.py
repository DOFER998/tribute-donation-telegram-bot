from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.common import env, escape_html
from src.filters import IsPrivate
from src.keyboards import get_donate_keyboard

router = Router()
router.message.filter(IsPrivate())


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        f'Привет, {escape_html(message.from_user.full_name)}!\n\n'
        '🏠 Мы собираем деньги на установку видеонаблюдения '
        f'на этажах нашего корпуса. Цель — <b>{env.fundraiser.title}</b>.\n\n'
        'Жми кнопку ниже чтобы поддержать сбор.'
    )
    await message.answer(text, reply_markup=get_donate_keyboard(env.tribute.donate_link))
