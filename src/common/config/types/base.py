from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseTypeConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        extra='ignore',
    )


class BaseEnvironment(BaseTypeConfig):
    pass
