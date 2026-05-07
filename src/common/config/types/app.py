from pydantic import SecretStr

from .base import BaseTypeConfig


class AppTypeConfig(BaseTypeConfig):
    domain: str
    host: str = '0.0.0.0'
    port: int = 9090
    secret_token: SecretStr
    debug: bool = False

    @property
    def webhook_url(self) -> str:
        return f'https://{self.domain}/telegram'
