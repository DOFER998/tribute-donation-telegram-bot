from pydantic import PostgresDsn, SecretStr

from .base import BaseTypeConfig


class PostgresTypeConfig(BaseTypeConfig):
    host: str
    port: int = 5432
    user: str
    password: SecretStr
    database: str

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
