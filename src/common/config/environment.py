from .types import (
    AdminTypeConfig,
    AppTypeConfig,
    BaseEnvironment,
    BotTypeConfig,
    DigestTypeConfig,
    PostgresTypeConfig,
    RedisTypeConfig,
    TributeTypeConfig,
)


class Environment(BaseEnvironment):
    bot: BotTypeConfig
    app: AppTypeConfig
    postgres: PostgresTypeConfig
    redis: RedisTypeConfig
    tribute: TributeTypeConfig
    digest: DigestTypeConfig
    admin: AdminTypeConfig


env = Environment()
