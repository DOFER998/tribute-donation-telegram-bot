from pydantic import HttpUrl, SecretStr

from ...constants import BOT_WEBHOOK_PATH
from .base import BaseTypeConfig


class AppTypeConfig(BaseTypeConfig):
    domain: str
    host: str
    port: int
    secret_token: SecretStr
    debug: bool = False

    @property
    def webhook_url(self) -> str:
        return HttpUrl.build(
            scheme='https',
            host=self.domain,
            path=BOT_WEBHOOK_PATH.lstrip('/'),
        ).unicode_string()
