from pydantic import ValidationError

from ..types import TributeRequest


def parse_tribute_request(data: dict) -> TributeRequest | None:
    try:
        return TributeRequest(**data)
    except ValidationError:
        return None
