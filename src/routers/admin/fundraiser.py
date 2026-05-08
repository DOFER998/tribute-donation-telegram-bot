from datetime import datetime, time

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage, InlineKeyboardMarkup, Message

from src.callback_data import FundraiserAction, FundraiserCreateCallback
from src.common import MOSCOW_TZ, format_date_moscow, parse_date_msk, render
from src.database import (
    DonationRepository,
    Fundraiser,
    FundraiserRepository,
    FundraiserStatus,
    async_session,
)
from src.filters import IsAdmin, IsPrivate
from src.keyboards import (
    get_active_menu_keyboard,
    get_cancel_keyboard,
    get_close_confirm_keyboard,
    get_confirm_create_keyboard,
    get_empty_menu_keyboard,
    get_topic_keyboard,
)
from src.services import FundraiserService
from src.services.fundraiser import require_fundraiser_id
from src.states import FundraiserCreate

from .export import build_donations_csv

router = Router()
router.message.filter(IsPrivate(), IsAdmin())
router.callback_query.filter(IsAdmin())


def _accessible_message(callback: CallbackQuery) -> Message | None:
    msg = callback.message
    if msg is None or isinstance(msg, InaccessibleMessage):
        return None
    return msg


async def _render_menu(fundraiser: Fundraiser | None) -> tuple[str, InlineKeyboardMarkup]:
    if fundraiser is None:
        return await render('fundraiser_menu_empty.html.j2'), get_empty_menu_keyboard()

    remaining = max(fundraiser.target_amount - fundraiser.current_amount, 0)
    text = await render(
        'fundraiser_menu_active.html.j2',
        fundraiser=fundraiser,
        remaining=remaining,
        start_date=format_date_moscow(fundraiser.start_date),
        end_date=format_date_moscow(fundraiser.end_date),
    )
    return text, get_active_menu_keyboard()


async def _show_menu(target: Message, state: FSMContext) -> None:
    await state.clear()
    async with async_session() as session:
        fundraiser = await FundraiserRepository(session).get_active()
    text, kb = await _render_menu(fundraiser)
    await target.answer(text, reply_markup=kb)


async def _show_confirm(target: Message, state: FSMContext) -> None:
    data = await state.get_data()
    end_date = datetime.fromisoformat(data['end_date_iso'])
    topic_id: int | None = data.get('topic_id')
    topic_label = f'#{topic_id}' if topic_id else 'общий чат'
    await state.set_state(FundraiserCreate.confirm)
    await target.answer(
        await render(
            'fundraiser_confirm.html.j2',
            title=data['title'],
            target_kopecks=data['target_kopecks'],
            end_date=end_date.strftime('%d.%m.%Y'),
            topic_label=topic_label,
        ),
        reply_markup=get_confirm_create_keyboard(),
    )


@router.message(Command('fundraiser'))
async def cmd_fundraiser(message: Message, state: FSMContext) -> None:
    await _show_menu(message, state)


@router.callback_query(FundraiserCreateCallback.filter(F.action == FundraiserAction.START_CREATE))
async def on_start_create(callback: CallbackQuery, state: FSMContext) -> None:
    msg = _accessible_message(callback)
    if msg is None:
        await callback.answer()
        return

    async with async_session() as session:
        existing = await FundraiserRepository(session).get_active()
    if existing:
        await msg.edit_reply_markup(reply_markup=None)
        text, kb = await _render_menu(existing)
        await msg.answer(text, reply_markup=kb)
        await callback.answer('Сбор уже активен', show_alert=True)
        return

    await state.set_state(FundraiserCreate.title)
    await msg.edit_reply_markup(reply_markup=None)
    await msg.answer(
        await render('fundraiser_ask_title.html.j2'),
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


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
    await state.set_state(FundraiserCreate.topic)
    await message.answer(
        await render('fundraiser_ask_topic.html.j2'),
        reply_markup=get_topic_keyboard(),
    )


@router.message(FundraiserCreate.topic)
async def topic_received(message: Message, state: FSMContext) -> None:
    topic_id: int | None = None

    if message.message_thread_id and (
        message.forward_origin is not None or message.forward_from_chat is not None
    ):
        topic_id = message.message_thread_id
    elif message.text:
        raw = message.text.strip()
        if raw.isdigit() and int(raw) > 0:
            topic_id = int(raw)

    if topic_id is None:
        await message.answer(
            await render('invalid_topic.html.j2'),
            reply_markup=get_topic_keyboard(),
        )
        return

    await state.update_data(topic_id=topic_id)
    await _show_confirm(message, state)


@router.callback_query(
    FundraiserCreateCallback.filter(F.action == FundraiserAction.SKIP_TOPIC),
    FundraiserCreate.topic,
)
async def on_skip_topic(callback: CallbackQuery, state: FSMContext) -> None:
    msg = _accessible_message(callback)
    if msg is None:
        await callback.answer()
        return

    await state.update_data(topic_id=None)
    await msg.edit_reply_markup(reply_markup=None)
    await _show_confirm(msg, state)
    await callback.answer()


@router.callback_query(
    FundraiserCreateCallback.filter(F.action == FundraiserAction.CONFIRM_CREATE),
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
        topic_id=data.get('topic_id'),
    )

    await msg.edit_reply_markup(reply_markup=None)
    await msg.answer(
        await render(
            'fundraiser_created.html.j2',
            fundraiser=fundraiser,
            end_date=end_date.strftime('%d.%m.%Y'),
        )
    )
    text, kb = await _render_menu(fundraiser)
    await msg.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(FundraiserCreateCallback.filter(F.action == FundraiserAction.CANCEL_CREATE))
async def cancel_create(callback: CallbackQuery, state: FSMContext) -> None:
    msg = _accessible_message(callback)
    await state.clear()
    if msg is None:
        await callback.answer()
        return
    await msg.edit_reply_markup(reply_markup=None)
    await msg.answer(await render('fundraiser_cancelled.html.j2'))
    async with async_session() as session:
        fundraiser = await FundraiserRepository(session).get_active()
    text, kb = await _render_menu(fundraiser)
    await msg.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(FundraiserCreateCallback.filter(F.action == FundraiserAction.BACK_TO_MENU))
async def on_back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    msg = _accessible_message(callback)
    if msg is None:
        await callback.answer()
        return
    await msg.edit_reply_markup(reply_markup=None)
    await _show_menu(msg, state)
    await callback.answer()


@router.callback_query(FundraiserCreateCallback.filter(F.action == FundraiserAction.CLOSE_REQUEST))
async def on_close_request(callback: CallbackQuery) -> None:
    msg = _accessible_message(callback)
    if msg is None:
        await callback.answer()
        return

    async with async_session() as session:
        fundraiser = await FundraiserRepository(session).get_active()

    if fundraiser is None:
        await msg.edit_reply_markup(reply_markup=None)
        await msg.answer(await render('no_active_fundraiser.html.j2'))
        await callback.answer()
        return

    await msg.edit_reply_markup(reply_markup=None)
    await msg.answer(
        await render('fundraiser_close_confirm.html.j2', fundraiser=fundraiser),
        reply_markup=get_close_confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(FundraiserCreateCallback.filter(F.action == FundraiserAction.CLOSE_CONFIRM))
async def on_close_confirm(callback: CallbackQuery, bot: Bot) -> None:
    msg = _accessible_message(callback)
    if msg is None:
        await callback.answer()
        return

    async with async_session() as session:
        fundraiser = await FundraiserRepository(session).get_active()

    if fundraiser is None:
        await msg.edit_reply_markup(reply_markup=None)
        await msg.answer(await render('no_active_fundraiser.html.j2'))
        await callback.answer()
        return

    fundraiser_id = require_fundraiser_id(fundraiser)
    service = FundraiserService(bot)
    await service.close_fundraiser(fundraiser_id, FundraiserStatus.CANCELLED)

    await msg.edit_reply_markup(reply_markup=None)
    await msg.answer(await render('fundraiser_closed_ok.html.j2', fundraiser_id=fundraiser_id))
    text, kb = await _render_menu(None)
    await msg.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(FundraiserCreateCallback.filter(F.action == FundraiserAction.EXPORT_CSV))
async def on_export_csv(callback: CallbackQuery) -> None:
    msg = _accessible_message(callback)
    if msg is None:
        await callback.answer()
        return

    async with async_session() as session:
        donations = await DonationRepository(session).get_all()

    if not donations:
        await msg.answer(await render('no_donations.html.j2'))
        await callback.answer()
        return

    await msg.answer_document(build_donations_csv(donations))
    await callback.answer('Готово')
