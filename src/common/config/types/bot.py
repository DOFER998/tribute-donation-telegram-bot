from pydantic import SecretStr

from .base import BaseTypeConfig


class BotTypeConfig(BaseTypeConfig):
    token: SecretStr
