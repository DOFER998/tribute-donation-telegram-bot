import csv
import io
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from src.common import format_amount, render
from src.database import DonationRepository, async_session
from src.filters import IsAdmin, IsPrivate

router = Router()
router.message.filter(IsPrivate(), IsAdmin())


@router.message(Command('donations_csv'))
async def cmd_export(message: Message) -> None:
    async with async_session() as session:
        donations = await DonationRepository(session).get_all()

    if not donations:
        await message.answer(await render('no_donations.html.j2'))
        return

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        'id', 'created_at', 'tribute_donation_request_id',
        'telegram_user_id', 'username', 'full_name',
        'amount_rub', 'currency', 'comment', 'is_anonymous',
    ])
    for d in donations:
        writer.writerow([
            d.id,
            d.created_at.isoformat(),
            d.tribute_donation_request_id,
            d.telegram_user_id or '',
            d.username or '',
            d.full_name or '',
            format_amount(d.amount),
            d.currency,
            (d.comment or '').replace('\n', ' '),
            d.is_anonymous,
        ])

    payload = buf.getvalue().encode('utf-8-sig')
    filename = f'donations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    await message.answer_document(BufferedInputFile(payload, filename=filename))
