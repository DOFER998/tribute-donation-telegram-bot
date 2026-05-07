from pydantic import SecretStr

from .base import BaseTypeConfig


class RedisTypeConfig(BaseTypeConfig):
    host: str
    port: int = 6379
    name: int = 0
    password: SecretStr | None = None

    @property
    def dsn(self) -> str:
        if self.password:
            return f'redis://:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.name}'
        return f'redis://{self.host}:{self.port}/{self.name}'
