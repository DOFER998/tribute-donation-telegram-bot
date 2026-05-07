from datetime import datetime, time, timedelta

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from src.common import MOSCOW_TZ, env, format_amount, parse_date_msk
from src.database import FundraiserRepository, FundraiserStatus, async_session
from src.filters import IsAdmin, IsPrivate
from src.services import FundraiserService

router = Router()
router.message.filter(IsPrivate(), IsAdmin())


@router.message(Command('fundraiser_create'))
async def cmd_create(message: Message, command: CommandObject, bot: Bot) -> None:
    """
    Использование: /fundraiser_create [end_date]
    end_date в формате DD.MM.YYYY (опц., default = +30 дней).
    Цель и название берутся из env (FUNDRAISER__TARGET, FUNDRAISER__TITLE).
    """
    async with async_session() as session:
        existing = await FundraiserRepository(session).get_active()
        if existing:
            await message.answer(
                f'Уже есть активный сбор #{existing.id}. Сначала закрой его (/fundraiser_close).'
            )
            return

    now = datetime.now(MOSCOW_TZ)
    if command.args:
        end_date = parse_date_msk(command.args.strip())
        if not end_date:
            await message.answer('Не понял дату. Формат: DD.MM.YYYY')
            return
        end_date = datetime.combine(end_date.date(), time(23, 59), tzinfo=MOSCOW_TZ)
    else:
        end_date = now + timedelta(days=30)

    service = FundraiserService(bot)
    f = await service.create_and_publish(
        target_amount=env.fundraiser.target,
        start_date=now,
        end_date=end_date,
        count_donations_from=now,
        title=env.fundraiser.title,
    )
    await message.answer(
        f'✅ Сбор #{f.id} создан\n'
        f'Цель: {format_amount(f.target_amount)} ₽\n'
        f'Окончание: {end_date.strftime("%d.%m.%Y")}'
    )


@router.message(Command('fundraiser_close'))
async def cmd_close(message: Message, bot: Bot) -> None:
    async with async_session() as session:
        f = await FundraiserRepository(session).get_active()
        if not f:
            await message.answer('Активных сборов нет.')
            return

    service = FundraiserService(bot)
    await service.close_fundraiser(f.id, FundraiserStatus.CANCELLED)
    await message.answer(f'✅ Сбор #{f.id} закрыт.')
