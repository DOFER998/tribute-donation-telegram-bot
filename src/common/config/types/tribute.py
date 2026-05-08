from pydantic import SecretStr

from .base import BaseTypeConfig


class TributeTypeConfig(BaseTypeConfig):
    api_key: SecretStr
    donate_link: str
    alert_group_id: int
