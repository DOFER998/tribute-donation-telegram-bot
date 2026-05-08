from pydantic import PostgresDsn, SecretStr

from .base import BaseTypeConfig


class PostgresTypeConfig(BaseTypeConfig):
    host: str = 'postgres'
    port: int = 5432
    user: str = 'fundraiser'
    password: SecretStr
    database: str = 'fundraiser_bot'

    @property
    def dsn(self) -> str:
        return PostgresDsn.build(
            scheme='postgresql+asyncpg',
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            path=self.database,
        ).unicode_string()
