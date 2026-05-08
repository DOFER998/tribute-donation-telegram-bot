import csv
import io
from datetime import datetime

from aiogram.types import BufferedInputFile

from src.common import format_amount
from src.database import Donation


def build_donations_csv(donations: list[Donation]) -> BufferedInputFile:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            'id',
            'created_at',
            'tribute_donation_request_id',
            'telegram_user_id',
            'username',
            'full_name',
            'amount_rub',
            'currency',
            'comment',
            'is_anonymous',
        ]
    )
    for d in donations:
        writer.writerow(
            [
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
            ]
        )

    payload = buf.getvalue().encode('utf-8-sig')
    filename = f'donations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return BufferedInputFile(payload, filename=filename)
