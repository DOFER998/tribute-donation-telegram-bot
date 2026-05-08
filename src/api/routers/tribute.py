import json
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from loguru import logger
from pydantic import ValidationError

from src.api.types import DonationPayload
from src.common import TEST_TRIBUTE_WEBHOOK_RESPONSE, TRIBUTE_WEBHOOK_PATH
from src.services import (
    DonationService,
    FundraiserService,
    NotificationQueueService,
)

from ..dependencies import (
    get_donation_service,
    get_fundraiser_service,
    get_notification_queue,
    verify_tribute_body,
)
from ..enums import TributeRequestType
from ..utils import parse_tribute_request

router = APIRouter()


@router.post(TRIBUTE_WEBHOOK_PATH)
async def tribute_webhook(
    body: Annotated[bytes, Depends(verify_tribute_body)],
    donation_service: Annotated[DonationService, Depends(get_donation_service)],
    notification_queue: Annotated[NotificationQueueService, Depends(get_notification_queue)],
    fundraiser_service: Annotated[FundraiserService, Depends(get_fundraiser_service)],
) -> Response:
    data = json.loads(body)

    if data == TEST_TRIBUTE_WEBHOOK_RESPONSE:
        logger.info('Test webhook received')
        return Response(content='OK')

    parsed = parse_tribute_request(data)
    if not parsed:
        logger.warning('Invalid tribute payload: {}', data)
        return Response(content='Invalid', status_code=400)

    if parsed.name not in (TributeRequestType.NEW_DONATION, TributeRequestType.RECURRENT_DONATION):
        logger.info('Skipping non-donation event: {}', parsed.name)
        return Response(content='OK')

    try:
        donation = DonationPayload.model_validate(parsed.payload)
    except ValidationError as e:
        logger.warning('Invalid donation payload: {}', e)
        return Response(content='Invalid donation payload', status_code=400)

    if donation.currency.lower() != 'rub':
        logger.warning('Non-RUB currency ignored: {}', donation.currency)
        return Response(content='OK')

    saved_now, is_anonymous = await donation_service.save(donation)
    if not saved_now:
        return Response(content='OK')

    await notification_queue.push(donation, is_anonymous)
    await fundraiser_service.update_progress(donation.amount)

    return Response(content='OK')
