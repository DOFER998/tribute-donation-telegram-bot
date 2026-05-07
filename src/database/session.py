from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.common import env

engine = create_async_engine(env.postgres.dsn, echo=False)

async_session = async_sessionmaker(engine, expire_on_commit=False)
