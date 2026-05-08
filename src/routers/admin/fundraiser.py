from datetime import datetime, time, timedelta

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from src.common import MOSCOW_TZ, env, parse_date_msk, render
from src.database import FundraiserRepository, FundraiserStatus, async_session
from src.filters import IsAdmin, IsPrivate
from src.services import FundraiserService

router = Router()
router.message.filter(IsPrivate(), IsAdmin())


@router.message(Command('fundraiser_create'))
async def cmd_create(message: Message, command: CommandObject, bot: Bot) -> None:
    async with async_session() as session:
        existing = await FundraiserRepository(session).get_active()
        if existing:
            await message.answer(
                await render('fundraiser_already_active.html.j2', fundraiser_id=existing.id)
            )
            return

    now = datetime.now(MOSCOW_TZ)
    if command.args:
        end_date = parse_date_msk(command.args.strip())
        if not end_date:
            await message.answer(await render('invalid_date.html.j2'))
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
        await render(
            'fundraiser_created.html.j2',
            fundraiser=f,
            end_date=end_date.strftime('%d.%m.%Y'),
        )
    )


@router.message(Command('fundraiser_close'))
async def cmd_close(message: Message, bot: Bot) -> None:
    async with async_session() as session:
        f = await FundraiserRepository(session).get_active()
        if not f:
            await message.answer(await render('no_active_fundraiser.html.j2'))
            return

    service = FundraiserService(bot)
    await service.close_fundraiser(f.id, FundraiserStatus.CANCELLED)
    await message.answer(await render('fundraiser_closed_ok.html.j2', fundraiser_id=f.id))
