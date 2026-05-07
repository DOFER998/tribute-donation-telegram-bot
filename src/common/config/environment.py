from .types import (
    AdminTypeConfig,
    AppTypeConfig,
    BaseEnvironment,
    BotTypeConfig,
    DigestTypeConfig,
    FundraiserTypeConfig,
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
    fundraiser: FundraiserTypeConfig
    digest: DigestTypeConfig
    admin: AdminTypeConfig


env = Environment()
