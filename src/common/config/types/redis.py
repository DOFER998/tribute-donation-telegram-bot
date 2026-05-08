from pydantic import RedisDsn, SecretStr

from .base import BaseTypeConfig


class RedisTypeConfig(BaseTypeConfig):
    host: str
    port: int
    name: int
    password: SecretStr

    @property
    def dsn(self) -> str:
        return RedisDsn.build(
            scheme='redis',
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            path=str(self.name),
        ).unicode_string()
