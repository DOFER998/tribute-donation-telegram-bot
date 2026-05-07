from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from testcontainers.postgres import PostgresContainer

import src.database.models  # noqa: F401  - регистрация моделей


@pytest_asyncio.fixture(scope='session', loop_scope='session')
async def postgres_container() -> AsyncIterator[PostgresContainer]:
    with PostgresContainer('postgres:16-alpine', driver='asyncpg') as pg:
        yield pg


@pytest_asyncio.fixture(scope='session', loop_scope='session')
async def engine(postgres_container):
    eng = create_async_engine(postgres_container.get_connection_url(), echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture(loop_scope='session')
async def db_session(engine) -> AsyncIterator[AsyncSession]:
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session
        for table in reversed(SQLModel.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()
