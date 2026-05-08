from datetime import datetime, time

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from src.callback_data import FundraiserAction, FundraiserCreateCallback
from src.common import MOSCOW_TZ, parse_date_msk, render
from src.database import FundraiserRepository, FundraiserStatus, async_session
from src.filters import IsAdmin, IsPrivate
from src.keyboards import get_cancel_keyboard, get_confirm_keyboard
from src.services import FundraiserService
from src.services.fundraiser import require_fundraiser_id
from src.states import FundraiserCreate

router = Router()
router.message.filter(IsPrivate(), IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command('fundraiser_create'))
async def cmd_create(message: Message, state: FSMContext) -> None:
    async with async_session() as session:
        existing = await FundraiserRepository(session).get_active()
    if existing:
        await message.answer(
            await render('fundraiser_already_active.html.j2', fundraiser_id=existing.id)
        )
        return

    await state.set_state(FundraiserCreate.title)
    await message.answer(
        await render('fundraiser_ask_title.html.j2'),
        reply_markup=get_cancel_keyboard(),
    )


@router.message(FundraiserCreate.title)
async def title_received(message: Message, state: FSMContext) -> None:
    title = (message.text or '').strip()
    if not title:
        await message.answer(
            await render('invalid_title.html.j2'),
            reply_markup=get_cancel_keyboard(),
        )
        return

    await state.update_data(title=title)
    await state.set_state(FundraiserCreate.target)
    await message.answer(
        await render('fundraiser_ask_target.html.j2'),
        reply_markup=get_cancel_keyboard(),
    )


@router.message(FundraiserCreate.target)
async def target_received(message: Message, state: FSMContext) -> None:
    raw = (message.text or '').strip().replace(' ', '').replace('_', '')
    try:
        rubles = int(raw)
    except ValueError:
        await message.answer(
            await render('invalid_target.html.j2'),
            reply_markup=get_cancel_keyboard(),
        )
        return

    if rubles <= 0:
        await message.answer(
            await render('invalid_target.html.j2'),
            reply_markup=get_cancel_keyboard(),
        )
        return

    await state.update_data(target_kopecks=rubles * 100)
    await state.set_state(FundraiserCreate.end_date)
    await message.answer(
        await render('fundraiser_ask_end_date.html.j2'),
        reply_markup=get_cancel_keyboard(),
    )


@router.message(FundraiserCreate.end_date)
async def end_date_received(message: Message, state: FSMContext) -> None:
    parsed = parse_date_msk((message.text or '').strip())
    if not parsed:
        await message.answer(
            await render('invalid_date.html.j2'),
            reply_markup=get_cancel_keyboard(),
        )
        return

    end_date = datetime.combine(parsed.date(), time(23, 59), tzinfo=MOSCOW_TZ)
    await state.update_data(end_date_iso=end_date.isoformat())
    await state.set_state(FundraiserCreate.confirm)

    data = await state.get_data()
    await message.answer(
        await render(
            'fundraiser_confirm.html.j2',
            title=data['title'],
            target_kopecks=data['target_kopecks'],
            end_date=end_date.strftime('%d.%m.%Y'),
        ),
        reply_markup=get_confirm_keyboard(),
    )


def _accessible_message(callback: CallbackQuery) -> Message | None:
    msg = callback.message
    if msg is None or isinstance(msg, InaccessibleMessage):
        return None
    return msg


@router.callback_query(
    FundraiserCreateCallback.filter(F.action == FundraiserAction.CONFIRM),
    FundraiserCreate.confirm,
)
async def confirm_create(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    msg = _accessible_message(callback)
    if msg is None:
        await callback.answer('Сообщение больше недоступно', show_alert=True)
        return

    data = await state.get_data()
    await state.clear()

    end_date = datetime.fromisoformat(data['end_date_iso'])
    now = datetime.now(MOSCOW_TZ)

    service = FundraiserService(bot)
    fundraiser = await service.create_and_publish(
        target_amount=data['target_kopecks'],
        start_date=now,
        end_date=end_date,
        count_donations_from=now,
        title=data['title'],
    )

    await msg.edit_reply_markup(reply_markup=None)
    await msg.answer(
        await render(
            'fundraiser_created.html.j2',
            fundraiser=fundraiser,
            end_date=end_date.strftime('%d.%m.%Y'),
        )
    )
    await callback.answer()


@router.callback_query(FundraiserCreateCallback.filter(F.action == FundraiserAction.CANCEL))
async def cancel_create(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    msg = _accessible_message(callback)
    if msg is None:
        await callback.answer()
        return
    await msg.edit_reply_markup(reply_markup=None)
    await msg.answer(await render('fundraiser_cancelled.html.j2'))
    await callback.answer()


@router.message(Command('fundraiser_close'))
async def cmd_close(message: Message, bot: Bot) -> None:
    async with async_session() as session:
        f = await FundraiserRepository(session).get_active()
        if not f:
            await message.answer(await render('no_active_fundraiser.html.j2'))
            return

    fundraiser_id = require_fundraiser_id(f)
    service = FundraiserService(bot)
    await service.close_fundraiser(fundraiser_id, FundraiserStatus.CANCELLED)
    await message.answer(
        await render('fundraiser_closed_ok.html.j2', fundraiser_id=fundraiser_id)
    )
