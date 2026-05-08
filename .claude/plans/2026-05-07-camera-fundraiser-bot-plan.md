# Camera Fundraiser Bot — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Telegram-бот для сбора донатов через Tribute на установку видеонаблюдения в подъезде. Принимает вебхуки, пишет в БД с полной инфой, шлёт алерты в топик, держит закреп прогресса, по достижении цели уведомляет, плюс ежедневная сводка админам.

**Architecture:** FastAPI + Granian принимает вебхук Tribute (HMAC-проверка) → сохраняет в Postgres с идемпотентностью → пушит в Redis-очередь → воркер aiogram шлёт алерт в топик. APScheduler закрывает истёкшие сборы и шлёт ежедневную сводку. Закреп прогресса auto-обновляется на каждом донате.

**Tech Stack:** Python 3.13, FastAPI, Granian, aiogram 3, SQLModel + asyncpg, Redis, Alembic, APScheduler, pydantic-settings, loguru. Деплой через docker-compose.

**Source reference:** Большая часть кода адаптирована из `/Users/c0mrade/PycharmProjects/tribute-bedolaga-telegram-bot`. Где написано «копия из источника» — взять файл as-is. Где «адаптация» — взять и изменить как указано.

---

## Phase 0: Подготовка

### Task 0: Бэкап текущего состояния и git init

**Files:**
- Modify: `/Users/c0mrade/PycharmProjects/tribute-donation-telegram-bot/`

- [ ] **Step 1: Перейти в директорию проекта**

```bash
cd /Users/c0mrade/PycharmProjects/tribute-donation-telegram-bot
```

- [ ] **Step 2: Инициализировать git если не инициализирован**

```bash
git init -b main 2>/dev/null || true
git status
```

- [ ] **Step 3: Удалить пустой `src/` если есть**

```bash
ls src/ 2>/dev/null && rmdir src/ 2>/dev/null || true
```

- [ ] **Step 4: Создать `.gitignore`**

```
# .gitignore
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/
*.egg-info/
dist/
build/
.env
.env.local
.idea/
.vscode/
.DS_Store
*.log
```

- [ ] **Step 5: Закоммитить пустой baseline**

```bash
git add .gitignore
git commit -m "chore: init repo with gitignore"
```

---

## Phase 1: Скаффолдинг и конфиг

### Task 1: pyproject.toml

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Записать pyproject.toml**

```toml
[project]
name = "tribute-donation-telegram-bot"
dynamic = ["version"]
description = "Telegram bot for camera-fundraiser via Tribute."
requires-python = ">=3.13"
dependencies = [
    "aiogram>=3.27.0",
    "alembic>=1.18.4",
    "apscheduler>=3.11.2",
    "asyncpg>=0.30.0",
    "fastapi>=0.136.0",
    "granian>=2.7.3",
    "greenlet>=3.4.0",
    "loguru>=0.7.3",
    "pydantic-settings>=2.13.1",
    "pytz>=2026.1.post1",
    "redis>=7.4.0",
    "sqlmodel>=0.0.38",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
    "httpx>=0.27",
    "testcontainers[postgres]>=4.9",
    "ruff>=0.15.11",
]

[tool.ruff]
line-length = 99
target-version = "py313"
exclude = [".git", ".venv", "alembic/versions"]
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "B", "I", "UP", "N", "SIM", "C4", "TID", "RET", "S", "BLE", "TRY"]
ignore = ["N805", "UP006", "UP035", "UP045", "TID252", "Q000", "Q003", "E501", "UP046"]

[tool.ruff.lint.isort]
combine-as-imports = true
known-first-party = ["src"]

[tool.ruff.format]
quote-style = "single"
indent-style = "space"

[tool.hatch.version]
path = "src/__meta__.py"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --strict-markers"

[tool.coverage.run]
source = ["src"]
omit = ["src/__meta__.py"]

[tool.coverage.report]
show_missing = true
fail_under = 80
```

- [ ] **Step 2: `uv sync`**

```bash
uv sync
```

Expected: `.venv/` создаётся, все deps ставятся.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add pyproject.toml with deps"
```

### Task 2: Дерево директорий и __init__.py

**Files:**
- Create: `src/__init__.py`, `src/__meta__.py`
- Create: пустые `__init__.py` в каждой подпапке

- [ ] **Step 1: Создать структуру директорий**

```bash
mkdir -p src/api/{routers,utils,types,enums}
mkdir -p src/services
mkdir -p src/database/{models,repositories}
mkdir -p src/routers/{private/messages,group/messages,admin}
mkdir -p src/keyboards/inline
mkdir -p src/filters
mkdir -p src/middlewares
mkdir -p src/common/{config/types,utils}
mkdir -p alembic/versions
mkdir -p tests/{unit,integration,e2e}
```

- [ ] **Step 2: Создать `src/__meta__.py`**

```python
__app_name__ = 'camera-fundraiser-bot'
__version__ = '0.1.0'
```

- [ ] **Step 3: Создать пустые `__init__.py`**

```bash
touch src/__init__.py \
      src/api/__init__.py src/api/routers/__init__.py \
      src/api/utils/__init__.py src/api/types/__init__.py \
      src/api/enums/__init__.py \
      src/services/__init__.py \
      src/database/__init__.py src/database/models/__init__.py \
      src/database/repositories/__init__.py \
      src/routers/__init__.py src/routers/private/__init__.py \
      src/routers/private/messages/__init__.py \
      src/routers/group/__init__.py src/routers/group/messages/__init__.py \
      src/routers/admin/__init__.py \
      src/keyboards/__init__.py src/keyboards/inline/__init__.py \
      src/filters/__init__.py \
      src/middlewares/__init__.py \
      src/common/__init__.py src/common/config/__init__.py \
      src/common/config/types/__init__.py src/common/utils/__init__.py \
      tests/__init__.py tests/unit/__init__.py \
      tests/integration/__init__.py tests/e2e/__init__.py
```

- [ ] **Step 4: Commit**

```bash
git add src/ tests/ alembic/
git commit -m "chore: project skeleton"
```

### Task 3: Конфиг — base type + bot/app/postgres/redis/admin

**Files:**
- Create: `src/common/config/types/base.py`, `bot.py`, `app.py`, `postgres.py`, `redis.py`, `admin.py`

- [ ] **Step 1: `base.py`**

```python
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
```

- [ ] **Step 2: `bot.py`**

```python
from pydantic import SecretStr

from .base import BaseTypeConfig


class BotTypeConfig(BaseTypeConfig):
    token: SecretStr
```

- [ ] **Step 3: `app.py`**

```python
from pydantic import SecretStr

from .base import BaseTypeConfig


class AppTypeConfig(BaseTypeConfig):
    domain: str
    host: str = '0.0.0.0'
    port: int = 9090
    secret_token: SecretStr
    debug: bool = False

    @property
    def webhook_url(self) -> str:
        return f'https://{self.domain}/telegram'
```

- [ ] **Step 4: `postgres.py`**

```python
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
```

- [ ] **Step 5: `redis.py`**

```python
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
```

- [ ] **Step 6: `admin.py`**

```python
from .base import BaseTypeConfig


class AdminTypeConfig(BaseTypeConfig):
    ids: list[int]

    @property
    def admin_ids(self) -> list[int]:
        return self.ids
```

- [ ] **Step 7: Commit**

```bash
git add src/common/config/types/{base,bot,app,postgres,redis,admin}.py
git commit -m "feat(config): base/bot/app/postgres/redis/admin types"
```

### Task 4: Конфиг — tribute / fundraiser / digest

**Files:**
- Create: `src/common/config/types/tribute.py`, `fundraiser.py`, `digest.py`

- [ ] **Step 1: `tribute.py`**

```python
from pydantic import SecretStr

from .base import BaseTypeConfig


class TributeTypeConfig(BaseTypeConfig):
    api_key: SecretStr
    donate_link: str
    alert_group_id: int
    alert_topic_id: int
    fundraiser_topic_id: int
```

- [ ] **Step 2: `fundraiser.py`**

```python
from .base import BaseTypeConfig


class FundraiserTypeConfig(BaseTypeConfig):
    target: int  # копейки
    title: str = 'Сбор'
```

- [ ] **Step 3: `digest.py`**

```python
from .base import BaseTypeConfig


class DigestTypeConfig(BaseTypeConfig):
    hour: int = 21  # MSK


```

- [ ] **Step 4: Commit**

```bash
git add src/common/config/types/{tribute,fundraiser,digest}.py
git commit -m "feat(config): tribute/fundraiser/digest types"
```

### Task 5: Aggregating types __init__ + environment.py

**Files:**
- Create: `src/common/config/types/__init__.py`, `src/common/config/environment.py`, `src/common/config/__init__.py`

- [ ] **Step 1: `types/__init__.py`**

```python
from .admin import AdminTypeConfig
from .app import AppTypeConfig
from .base import BaseEnvironment, BaseTypeConfig
from .bot import BotTypeConfig
from .digest import DigestTypeConfig
from .fundraiser import FundraiserTypeConfig
from .postgres import PostgresTypeConfig
from .redis import RedisTypeConfig
from .tribute import TributeTypeConfig

__all__ = [
    'AdminTypeConfig',
    'AppTypeConfig',
    'BaseEnvironment',
    'BaseTypeConfig',
    'BotTypeConfig',
    'DigestTypeConfig',
    'FundraiserTypeConfig',
    'PostgresTypeConfig',
    'RedisTypeConfig',
    'TributeTypeConfig',
]
```

- [ ] **Step 2: `environment.py`**

```python
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
```

- [ ] **Step 3: `config/__init__.py`**

```python
from .environment import Environment, env

__all__ = ['Environment', 'env']
```

- [ ] **Step 4: Commit**

```bash
git add src/common/config/
git commit -m "feat(config): assemble Environment"
```

### Task 6: Constants + utils

**Files:**
- Create: `src/common/constants.py`, `src/common/utils/datetime.py`, `src/common/utils/formatting.py`, `src/common/utils/logging.py`, `src/common/utils/telegram.py`, `src/common/utils/__init__.py`, `src/common/__init__.py`

- [ ] **Step 1: `constants.py`**

```python
from typing import Final

from aiogram.types import BotCommand
from pytz import BaseTzInfo, timezone

BOT_WEBHOOK_PATH: Final[str] = '/telegram'
TRIBUTE_WEBHOOK_PATH: Final[str] = '/tribute'
TEST_TRIBUTE_WEBHOOK_RESPONSE: Final[dict[str, str]] = {'test_event': 'test_event'}

BOT_PRIVATE_COMMANDS: Final[list[BotCommand]] = [
    BotCommand(command='start', description='Главное меню'),
]

MOSCOW_TZ: Final[BaseTzInfo] = timezone('Europe/Moscow')

NOTIFICATION_QUEUE_KEY: Final[str] = 'tribute:notifications'

TELEGRAM_MESSAGE_MAX_LENGTH: Final[int] = 4096
```

- [ ] **Step 2: `utils/datetime.py`**

```python
from datetime import UTC, datetime

from src.common.constants import MOSCOW_TZ


def utc_now() -> datetime:
    return datetime.now(UTC)


def format_date_moscow(dt: datetime) -> str:
    return dt.astimezone(MOSCOW_TZ).strftime('%d.%m.%Y')


def format_datetime_moscow(dt: datetime) -> str:
    return dt.astimezone(MOSCOW_TZ).strftime('%d.%m.%Y %H:%M')


def parse_date_msk(text: str) -> datetime | None:
    formats = ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
    for fmt in formats:
        try:
            dt = datetime.strptime(text.strip(), fmt)
            return dt.replace(tzinfo=MOSCOW_TZ)
        except ValueError:
            continue
    return None
```

- [ ] **Step 3: `utils/formatting.py`**

```python
from html import escape


def format_amount(kopecks: int) -> str:
    """копейки -> '1 234' / '1 234.56'"""
    rubles = kopecks / 100
    if rubles == int(rubles):
        return f'{int(rubles):,}'.replace(',', ' ')
    return f'{rubles:,.2f}'.replace(',', ' ').rstrip('0').rstrip('.')


def calc_progress(current: int, target: int, bar_length: int = 10) -> tuple[int, str]:
    percent = min(int(current * 100 / target), 100) if target > 0 else 0
    filled = int(bar_length * percent / 100)
    empty = bar_length - filled
    bar = '⟨' + '▰' * filled + '▱' * empty + '⟩'
    return percent, bar


def escape_html(text: str) -> str:
    return escape(text, quote=False)
```

- [ ] **Step 4: `utils/logging.py`**

```python
import sys

from loguru import logger


def setup_logging(debug: bool = False) -> None:
    logger.remove()
    level = 'DEBUG' if debug else 'INFO'
    logger.add(
        sys.stderr,
        level=level,
        format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
               '<level>{level: <8}</level> | '
               '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>',
    )
```

- [ ] **Step 5: `utils/telegram.py`**

```python
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger


async def get_user_display_name(bot: Bot, chat_id: int, user_id: int) -> tuple[str | None, str | None]:
    """Вернуть (username, full_name) для пользователя в чате. None если не удалось получить."""
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        user = member.user
        return user.username, user.full_name
    except TelegramAPIError as e:
        logger.warning('Failed to get chat member: chat_id={}, user_id={}, err={}', chat_id, user_id, e)
        return None, None
```

- [ ] **Step 6: `utils/__init__.py`**

```python
from .datetime import format_date_moscow, format_datetime_moscow, parse_date_msk, utc_now
from .formatting import calc_progress, escape_html, format_amount
from .logging import setup_logging
from .telegram import get_user_display_name

__all__ = [
    'calc_progress',
    'escape_html',
    'format_amount',
    'format_date_moscow',
    'format_datetime_moscow',
    'get_user_display_name',
    'parse_date_msk',
    'setup_logging',
    'utc_now',
]
```

- [ ] **Step 7: `common/__init__.py`**

```python
from .config import env
from .constants import (
    BOT_PRIVATE_COMMANDS,
    BOT_WEBHOOK_PATH,
    MOSCOW_TZ,
    NOTIFICATION_QUEUE_KEY,
    TELEGRAM_MESSAGE_MAX_LENGTH,
    TEST_TRIBUTE_WEBHOOK_RESPONSE,
    TRIBUTE_WEBHOOK_PATH,
)
from .utils import (
    calc_progress,
    escape_html,
    format_amount,
    format_date_moscow,
    format_datetime_moscow,
    get_user_display_name,
    parse_date_msk,
    setup_logging,
    utc_now,
)

__all__ = [
    'BOT_PRIVATE_COMMANDS',
    'BOT_WEBHOOK_PATH',
    'MOSCOW_TZ',
    'NOTIFICATION_QUEUE_KEY',
    'TELEGRAM_MESSAGE_MAX_LENGTH',
    'TEST_TRIBUTE_WEBHOOK_RESPONSE',
    'TRIBUTE_WEBHOOK_PATH',
    'calc_progress',
    'env',
    'escape_html',
    'format_amount',
    'format_date_moscow',
    'format_datetime_moscow',
    'get_user_display_name',
    'parse_date_msk',
    'setup_logging',
    'utc_now',
]
```

- [ ] **Step 8: Commit**

```bash
git add src/common/
git commit -m "feat(common): constants and utils"
```

### Task 7: .env.example, Dockerfile, docker-compose

**Files:**
- Create: `.env.example`, `Dockerfile`, `docker-compose.local.yml`, `docker-compose.prod.yml`, `Makefile`

- [ ] **Step 1: `.env.example`**

```ini
# Bot
BOT__TOKEN=change_me

# App
APP__DOMAIN=change_me.example.com
APP__HOST=0.0.0.0
APP__PORT=9090
APP__SECRET_TOKEN=change_me_random_secret
APP__DEBUG=false

# Postgres
POSTGRES__HOST=postgres
POSTGRES__PORT=5432
POSTGRES__USER=fundraiser
POSTGRES__PASSWORD=change_me
POSTGRES__DATABASE=fundraiser_bot

# Redis
REDIS__HOST=redis
REDIS__PORT=6379
REDIS__NAME=0
REDIS__PASSWORD=change_me

# Tribute
TRIBUTE__API_KEY=change_me
TRIBUTE__DONATE_LINK=https://tribute.tg/...
TRIBUTE__ALERT_GROUP_ID=-1001234567890
TRIBUTE__ALERT_TOPIC_ID=2
TRIBUTE__FUNDRAISER_TOPIC_ID=3

# Fundraiser
FUNDRAISER__TARGET=69800000
FUNDRAISER__TITLE=Камеры для 1 корпуса

# Digest
DIGEST__HOUR=21

# Admin (JSON list)
ADMIN__IDS=[123456789]
```

- [ ] **Step 2: `Dockerfile`**

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini ./

CMD ["uv", "run", "python", "-m", "src.main"]
```

- [ ] **Step 3: `docker-compose.local.yml`**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES__USER}
      POSTGRES_PASSWORD: ${POSTGRES__PASSWORD}
      POSTGRES_DB: ${POSTGRES__DATABASE}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES__USER}"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--requirepass", "${REDIS__PASSWORD}"]
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS__PASSWORD}", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:
  redisdata:
```

- [ ] **Step 4: `docker-compose.prod.yml`**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES__USER}
      POSTGRES_PASSWORD: ${POSTGRES__PASSWORD}
      POSTGRES_DB: ${POSTGRES__DATABASE}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES__USER}"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--requirepass", "${REDIS__PASSWORD}"]
    volumes:
      - redisdata:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS__PASSWORD}", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  bot:
    build: .
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "9090:9090"
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
```

- [ ] **Step 5: `Makefile`**

```makefile
.PHONY: install lint format test up down migrate revision

install:
	uv sync

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

test:
	uv run pytest --cov=src --cov-report=term-missing

up:
	docker compose -f docker-compose.local.yml up -d

down:
	docker compose -f docker-compose.local.yml down

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "$(msg)"
```

- [ ] **Step 6: Commit**

```bash
git add .env.example Dockerfile docker-compose.local.yml docker-compose.prod.yml Makefile
git commit -m "chore: docker-compose, Dockerfile, Makefile"
```

### Task 8: Alembic init + env.py

**Files:**
- Create: `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`

- [ ] **Step 1: `alembic.ini`**

Скопировать из `/Users/c0mrade/PycharmProjects/tribute-bedolaga-telegram-bot/alembic.ini` без изменений (уже подходит).

```bash
cp /Users/c0mrade/PycharmProjects/tribute-bedolaga-telegram-bot/alembic.ini alembic.ini
```

- [ ] **Step 2: `alembic/script.py.mako`**

```bash
cp /Users/c0mrade/PycharmProjects/tribute-bedolaga-telegram-bot/alembic/script.py.mako alembic/script.py.mako
```

- [ ] **Step 3: `alembic/env.py`**

Адаптация: импорт моделей из нашего проекта.

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from src.common import env as app_env
from src.database.models import Donation, Fundraiser  # noqa: F401  -- регистрация моделей

config = context.config
config.set_main_option('sqlalchemy.url', app_env.postgres.dsn)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Commit (не миграция, только конфиг)**

```bash
git add alembic.ini alembic/env.py alembic/script.py.mako
git commit -m "chore(alembic): init config + env"
```

---

## Phase 2: База данных

### Task 9: TimestampMixin

**Files:**
- Create: `src/database/models/mixins.py`

- [ ] **Step 1: Содержимое**

```python
from datetime import datetime

from sqlalchemy import TIMESTAMP
from sqlmodel import Field

from src.common import utc_now


class TimestampMixin:
    created_at: datetime = Field(
        default_factory=utc_now, sa_type=TIMESTAMP(timezone=True), index=True
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=TIMESTAMP(timezone=True),
        sa_column_kwargs={'onupdate': utc_now},
    )
```

- [ ] **Step 2: Commit**

```bash
git add src/database/models/mixins.py
git commit -m "feat(db): TimestampMixin"
```

### Task 10: Donation model (расширенная)

**Files:**
- Create: `src/database/models/donation.py`

- [ ] **Step 1: Содержимое**

```python
from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel

from .mixins import TimestampMixin


class Donation(TimestampMixin, SQLModel, table=True):
    __tablename__ = 'donations'

    id: int | None = Field(default=None, primary_key=True)
    tribute_donation_request_id: int = Field(sa_type=BigInteger, unique=True, index=True)
    telegram_user_id: int | None = Field(default=None, sa_type=BigInteger, index=True)
    username: str | None = Field(default=None, max_length=64)
    full_name: str | None = Field(default=None, max_length=256)
    amount: int = Field(sa_type=BigInteger)
    currency: str = Field(default='rub', index=True, max_length=3)
    comment: str | None = Field(default=None)
    is_anonymous: bool = Field(default=False, index=True)
```

- [ ] **Step 2: Commit**

```bash
git add src/database/models/donation.py
git commit -m "feat(db): Donation model with full info + idempotency key"
```

### Task 11: Fundraiser model

**Files:**
- Create: `src/database/models/fundraiser.py`

- [ ] **Step 1: Содержимое (копия из источника)**

```python
from datetime import datetime

from sqlalchemy import TIMESTAMP, BigInteger
from sqlmodel import Field, SQLModel

from .mixins import TimestampMixin


class FundraiserStatus:
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class Fundraiser(TimestampMixin, SQLModel, table=True):
    __tablename__ = 'fundraisers'

    id: int | None = Field(default=None, primary_key=True)
    title: str | None = Field(default=None)
    target_amount: int = Field(sa_type=BigInteger)
    current_amount: int = Field(default=0, sa_type=BigInteger)
    start_date: datetime = Field(sa_type=TIMESTAMP(timezone=True))
    end_date: datetime = Field(sa_type=TIMESTAMP(timezone=True))
    count_donations_from: datetime = Field(sa_type=TIMESTAMP(timezone=True))
    channel_message_id: int | None = Field(default=None, sa_type=BigInteger)
    status: str = Field(default=FundraiserStatus.ACTIVE, index=True)
```

- [ ] **Step 2: `models/__init__.py`**

```python
from .donation import Donation
from .fundraiser import Fundraiser, FundraiserStatus
from .mixins import TimestampMixin

__all__ = ['Donation', 'Fundraiser', 'FundraiserStatus', 'TimestampMixin']
```

- [ ] **Step 3: Commit**

```bash
git add src/database/models/fundraiser.py src/database/models/__init__.py
git commit -m "feat(db): Fundraiser model"
```

### Task 12: Database session

**Files:**
- Create: `src/database/session.py`

- [ ] **Step 1: Содержимое**

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.common import env

engine = create_async_engine(env.postgres.dsn, echo=False)

async_session = async_sessionmaker(engine, expire_on_commit=False)
```

- [ ] **Step 2: Commit**

```bash
git add src/database/session.py
git commit -m "feat(db): async session"
```

### Task 13: Donation repository

**Files:**
- Create: `tests/unit/test_donation_repository.py`
- Create: `src/database/repositories/donation.py`

- [ ] **Step 1: Test (TDD) — пока stub, реальные интеграционные тесты будут в Phase 7**

```python
# tests/unit/test_donation_repository.py
def test_donation_repo_module_imports():
    from src.database.repositories.donation import DonationRepository  # noqa: F401
```

- [ ] **Step 2: Run test, FAIL (модуль ещё нет)**

```bash
uv run pytest tests/unit/test_donation_repository.py -v
```

Expected: ImportError.

- [ ] **Step 3: `repositories/donation.py`**

```python
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Donation


class DonationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_donation(
        self,
        *,
        tribute_donation_request_id: int,
        amount: int,
        currency: str = 'rub',
        telegram_user_id: int | None = None,
        username: str | None = None,
        full_name: str | None = None,
        comment: str | None = None,
        is_anonymous: bool = False,
    ) -> Donation | None:
        """Идемпотентная вставка. Возвращает None если запись уже была."""
        stmt = (
            pg_insert(Donation.__table__)
            .values(
                tribute_donation_request_id=tribute_donation_request_id,
                telegram_user_id=telegram_user_id,
                username=username,
                full_name=full_name,
                amount=amount,
                currency=currency,
                comment=comment,
                is_anonymous=is_anonymous,
            )
            .on_conflict_do_nothing(index_elements=['tribute_donation_request_id'])
            .returning(Donation.__table__)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        row = result.first()
        if row is None:
            return None
        return Donation(**dict(row._mapping))

    async def get_user_total(self, telegram_user_id: int) -> int:
        query = select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.telegram_user_id == telegram_user_id,
            Donation.is_anonymous.is_(False),
        )
        return (await self.session.execute(query)).scalar() or 0

    async def get_user_rank(self, telegram_user_id: int) -> int | None:
        user_total = await self.get_user_total(telegram_user_id)
        if user_total == 0:
            return None

        subquery = (
            select(
                Donation.telegram_user_id,
                func.sum(Donation.amount).label('total'),
            )
            .where(
                Donation.is_anonymous.is_(False),
                Donation.telegram_user_id.isnot(None),
            )
            .group_by(Donation.telegram_user_id)
            .subquery()
        )
        rank_query = select(func.count()).where(subquery.c.total > user_total)
        users_above = (await self.session.execute(rank_query)).scalar() or 0
        return users_above + 1

    async def get_top_donors(self, limit: int = 3) -> list[dict]:
        query = (
            select(
                Donation.telegram_user_id,
                func.max(Donation.username).label('username'),
                func.max(Donation.full_name).label('full_name'),
                func.sum(Donation.amount).label('total_amount'),
            )
            .where(
                Donation.is_anonymous.is_(False),
                Donation.telegram_user_id.isnot(None),
            )
            .group_by(Donation.telegram_user_id)
            .order_by(func.sum(Donation.amount).desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [
            {
                'telegram_user_id': r.telegram_user_id,
                'username': r.username,
                'full_name': r.full_name,
                'total_amount': r.total_amount,
            }
            for r in result.all()
        ]

    async def get_stats_for_period(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> dict:
        conds = []
        if start:
            conds.append(Donation.created_at >= start)
        if end:
            conds.append(Donation.created_at < end)

        total = (
            await self.session.execute(
                select(func.coalesce(func.sum(Donation.amount), 0)).where(*conds)
            )
        ).scalar() or 0
        count = (
            await self.session.execute(select(func.count()).where(*conds))
        ).scalar() or 0
        unique = (
            await self.session.execute(
                select(func.count(func.distinct(Donation.telegram_user_id))).where(
                    Donation.telegram_user_id.isnot(None),
                    Donation.is_anonymous.is_(False),
                    *conds,
                )
            )
        ).scalar() or 0
        return {'total_amount': total, 'count': count, 'unique_donors': unique}

    async def get_all(self) -> list[Donation]:
        result = await self.session.execute(
            select(Donation).order_by(Donation.created_at.desc())
        )
        return list(result.scalars().all())
```

- [ ] **Step 4: Run test, PASS**

```bash
uv run pytest tests/unit/test_donation_repository.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/database/repositories/donation.py tests/unit/test_donation_repository.py
git commit -m "feat(db): DonationRepository with idempotent upsert"
```

### Task 14: Fundraiser repository

**Files:**
- Create: `src/database/repositories/fundraiser.py`, `src/database/repositories/__init__.py`, `src/database/__init__.py`

- [ ] **Step 1: `repositories/fundraiser.py`** (адаптация — убрана зависимость от `currency=='rub'` фильтра, у нас всегда рубли)

```python
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Donation, Fundraiser, FundraiserStatus


class FundraiserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        target_amount: int,
        start_date: datetime,
        end_date: datetime,
        count_donations_from: datetime,
        title: str | None = None,
    ) -> Fundraiser:
        fundraiser = Fundraiser(
            title=title,
            target_amount=target_amount,
            start_date=start_date,
            end_date=end_date,
            count_donations_from=count_donations_from,
        )
        self.session.add(fundraiser)
        await self.session.commit()
        await self.session.refresh(fundraiser)
        return fundraiser

    async def get_active(self) -> Fundraiser | None:
        q = select(Fundraiser).where(Fundraiser.status == FundraiserStatus.ACTIVE)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def get_by_id(self, fundraiser_id: int) -> Fundraiser | None:
        q = select(Fundraiser).where(Fundraiser.id == fundraiser_id)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def update_amount(self, fundraiser_id: int, amount: int) -> Fundraiser | None:
        f = await self.get_by_id(fundraiser_id)
        if f:
            f.current_amount = amount
            await self.session.commit()
            await self.session.refresh(f)
        return f

    async def add_amount(self, fundraiser_id: int, delta: int) -> Fundraiser | None:
        f = await self.get_by_id(fundraiser_id)
        if f:
            f.current_amount += delta
            await self.session.commit()
            await self.session.refresh(f)
        return f

    async def set_message_id(self, fundraiser_id: int, message_id: int) -> Fundraiser | None:
        f = await self.get_by_id(fundraiser_id)
        if f:
            f.channel_message_id = message_id
            await self.session.commit()
            await self.session.refresh(f)
        return f

    async def close(self, fundraiser_id: int, status: str = FundraiserStatus.COMPLETED) -> Fundraiser | None:
        f = await self.get_by_id(fundraiser_id)
        if f:
            f.status = status
            await self.session.commit()
            await self.session.refresh(f)
        return f

    async def get_donations_sum_from_date(self, from_date: datetime) -> int:
        q = select(func.coalesce(func.sum(Donation.amount), 0)).where(Donation.created_at >= from_date)
        return (await self.session.execute(q)).scalar() or 0

    async def get_expired_active(self, now: datetime) -> list[Fundraiser]:
        q = select(Fundraiser).where(
            Fundraiser.status == FundraiserStatus.ACTIVE, Fundraiser.end_date <= now
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())
```

- [ ] **Step 2: `repositories/__init__.py`**

```python
from .donation import DonationRepository
from .fundraiser import FundraiserRepository

__all__ = ['DonationRepository', 'FundraiserRepository']
```

- [ ] **Step 3: `database/__init__.py`**

```python
from .models import Donation, Fundraiser, FundraiserStatus
from .repositories import DonationRepository, FundraiserRepository
from .session import async_session, engine

__all__ = [
    'Donation',
    'DonationRepository',
    'Fundraiser',
    'FundraiserRepository',
    'FundraiserStatus',
    'async_session',
    'engine',
]
```

- [ ] **Step 4: Commit**

```bash
git add src/database/
git commit -m "feat(db): FundraiserRepository + database package"
```

### Task 15: Initial migration

**Files:**
- Create: `alembic/versions/0001_initial.py` (через autogenerate)

- [ ] **Step 1: Запустить локальный postgres**

```bash
cp .env.example .env  # заполнить секреты для локалки
docker compose -f docker-compose.local.yml up -d postgres
```

- [ ] **Step 2: Сгенерировать миграцию**

```bash
uv run alembic revision --autogenerate -m "initial"
```

- [ ] **Step 3: Проверить файл `alembic/versions/*_initial.py` — должен содержать создание `donations` и `fundraisers` со всеми колонками + индексы + UNIQUE на `tribute_donation_request_id`.**

- [ ] **Step 4: Применить миграцию**

```bash
uv run alembic upgrade head
```

- [ ] **Step 5: Проверить через psql**

```bash
docker compose -f docker-compose.local.yml exec postgres \
  psql -U fundraiser -d fundraiser_bot -c '\d+ donations'
```

Ожидаем колонки: `id, tribute_donation_request_id, telegram_user_id, username, full_name, amount, currency, comment, is_anonymous, created_at, updated_at`.

- [ ] **Step 6: Commit**

```bash
git add alembic/versions/
git commit -m "feat(db): initial migration"
```

---

## Phase 3: Tribute Webhook API

### Task 16: API types — base + payload

**Files:**
- Create: `src/api/types/base.py`, `donation_payload.py`, `tribute_request.py`, `__init__.py`
- Create: `src/api/enums/tribute_request_type.py`, `__init__.py`

- [ ] **Step 1: `types/base.py`**

```python
from pydantic import BaseModel, ConfigDict


class BaseObject(BaseModel):
    model_config = ConfigDict(extra='ignore', populate_by_name=True)
```

- [ ] **Step 2: `enums/tribute_request_type.py`**

```python
from enum import StrEnum


class TributeRequestType(StrEnum):
    NEW_DONATION = 'new_donation'
    RECURRENT_DONATION = 'recurrent_donation'
    NEW_SUBSCRIPTION = 'new_subscription'
    CANCELLED_SUBSCRIPTION = 'cancelled_subscription'
```

- [ ] **Step 3: `enums/__init__.py`**

```python
from .tribute_request_type import TributeRequestType

__all__ = ['TributeRequestType']
```

- [ ] **Step 4: `types/donation_payload.py`** (копия с минимальной чисткой)

```python
from typing import Optional

from pydantic import Field

from .base import BaseObject


class DonationPayload(BaseObject):
    donation_request_id: int
    donation_name: str
    message: Optional[str] = None
    period: str = ''
    amount: int
    currency: str
    anonymously: bool = False
    web_app_link: str = ''
    trb_user_id: Optional[str] = None
    user_id: Optional[int] = Field(default=None, deprecated=True)
    telegram_user_id: Optional[int] = None
```

- [ ] **Step 5: `types/tribute_request.py`**

```python
from datetime import datetime

from ..enums import TributeRequestType
from .base import BaseObject
from .donation_payload import DonationPayload


class TributeRequest(BaseObject):
    name: TributeRequestType
    created_at: datetime
    sent_at: datetime
    payload: DonationPayload
```

- [ ] **Step 6: `types/__init__.py`**

```python
from .base import BaseObject
from .donation_payload import DonationPayload
from .tribute_request import TributeRequest

__all__ = ['BaseObject', 'DonationPayload', 'TributeRequest']
```

- [ ] **Step 7: Commit**

```bash
git add src/api/types/ src/api/enums/
git commit -m "feat(api): pydantic types and enums"
```

### Task 17: Signature verification (TDD)

**Files:**
- Create: `tests/unit/test_signature.py`
- Create: `src/api/utils/signature.py`, `src/api/utils/__init__.py`

- [ ] **Step 1: `tests/unit/test_signature.py`**

```python
import hashlib
import hmac

import pytest

from src.api.utils.signature import verify_tribute_signature


SECRET = 'test-secret'


def _sign(body: bytes, secret: str = SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_returns_true():
    body = b'{"name":"new_donation"}'
    sig = _sign(body)
    assert verify_tribute_signature(body, sig, SECRET) is True


def test_invalid_signature_returns_false():
    body = b'{"name":"new_donation"}'
    assert verify_tribute_signature(body, 'deadbeef', SECRET) is False


def test_missing_signature_returns_false():
    body = b'{"name":"new_donation"}'
    assert verify_tribute_signature(body, None, SECRET) is False


def test_wrong_secret_returns_false():
    body = b'{"name":"new_donation"}'
    sig = _sign(body, 'other-secret')
    assert verify_tribute_signature(body, sig, SECRET) is False


def test_tampered_body_returns_false():
    body = b'{"name":"new_donation"}'
    sig = _sign(body)
    assert verify_tribute_signature(b'{"name":"hacked"}', sig, SECRET) is False
```

- [ ] **Step 2: Run test, FAIL**

```bash
uv run pytest tests/unit/test_signature.py -v
```

Expected: ImportError.

- [ ] **Step 3: `src/api/utils/signature.py`**

```python
import hashlib
import hmac


def verify_tribute_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
```

- [ ] **Step 4: `src/api/utils/__init__.py`**

```python
from .signature import verify_tribute_signature

__all__ = ['verify_tribute_signature']
```

- [ ] **Step 5: Run test, PASS**

```bash
uv run pytest tests/unit/test_signature.py -v
```

- [ ] **Step 6: Commit**

```bash
git add src/api/utils/ tests/unit/test_signature.py
git commit -m "feat(api): HMAC signature verification with tests"
```

### Task 18: Parser (TDD)

**Files:**
- Create: `tests/unit/test_parser.py`
- Create: `src/api/utils/parser.py`

- [ ] **Step 1: `tests/unit/test_parser.py`**

```python
from src.api.enums import TributeRequestType
from src.api.utils.parser import parse_tribute_request


def _valid_payload():
    return {
        'name': 'new_donation',
        'created_at': '2026-05-07T12:00:00Z',
        'sent_at': '2026-05-07T12:00:01Z',
        'payload': {
            'donation_request_id': 12345,
            'donation_name': 'Камеры для 1 корпуса',
            'message': 'удачи',
            'period': '',
            'amount': 200000,
            'currency': 'rub',
            'anonymously': False,
            'web_app_link': '',
            'telegram_user_id': 99,
        },
    }


def test_parse_valid_donation():
    req = parse_tribute_request(_valid_payload())
    assert req is not None
    assert req.name == TributeRequestType.NEW_DONATION
    assert req.payload.amount == 200000
    assert req.payload.message == 'удачи'


def test_parse_invalid_returns_none():
    assert parse_tribute_request({'foo': 'bar'}) is None


def test_parse_unknown_event_returns_none():
    data = _valid_payload()
    data['name'] = 'totally_unknown_event'
    assert parse_tribute_request(data) is None
```

- [ ] **Step 2: Run, FAIL**

- [ ] **Step 3: `src/api/utils/parser.py`**

```python
from pydantic import ValidationError

from ..types import TributeRequest


def parse_tribute_request(data: dict) -> TributeRequest | None:
    try:
        return TributeRequest(**data)
    except ValidationError:
        return None
```

- [ ] **Step 4: Обновить `src/api/utils/__init__.py`**

```python
from .parser import parse_tribute_request
from .signature import verify_tribute_signature

__all__ = ['parse_tribute_request', 'verify_tribute_signature']
```

- [ ] **Step 5: Run, PASS**

```bash
uv run pytest tests/unit/test_parser.py -v
```

- [ ] **Step 6: Commit**

```bash
git add src/api/utils/parser.py src/api/utils/__init__.py tests/unit/test_parser.py
git commit -m "feat(api): payload parser with tests"
```

### Task 19: API dependencies

**Files:**
- Create: `src/api/dependencies.py`

- [ ] **Step 1: Содержимое**

```python
from typing import Annotated

from aiogram import Bot, Dispatcher
from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from src.common import env

from .utils import verify_tribute_signature as _verify


def get_bot(request: Request) -> Bot:
    return request.app.state.bot


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_dispatcher(request: Request) -> Dispatcher:
    return request.app.state.dispatcher


async def verify_telegram_secret(request: Request) -> None:
    secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
    if secret != env.app.secret_token.get_secret_value():
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid secret token')


async def verify_tribute_body(request: Request) -> bytes:
    body = await request.body()
    if not body:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Empty body')

    sig = request.headers.get('trbt-signature')
    if not _verify(body, sig, env.tribute.api_key.get_secret_value()):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid signature')

    return body


def get_donation_service(bot: Annotated[Bot, Depends(get_bot)]):
    from src.services import DonationService
    return DonationService(bot)


def get_notification_queue(request: Request):
    return request.app.state.notification_queue


def get_fundraiser_service(bot: Annotated[Bot, Depends(get_bot)]):
    from src.services import FundraiserService
    return FundraiserService(bot)
```

- [ ] **Step 2: Commit**

```bash
git add src/api/dependencies.py
git commit -m "feat(api): FastAPI DI dependencies"
```

---

## Phase 4: Сервисы

### Task 20: NotificationQueueService

**Files:**
- Create: `src/services/notification_queue.py`

- [ ] **Step 1: Содержимое**

```python
import asyncio
import json
from typing import Final

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from loguru import logger
from redis.asyncio import Redis

from src.api.types import DonationPayload
from src.common import (
    NOTIFICATION_QUEUE_KEY,
    env,
    escape_html,
    format_amount,
    get_user_display_name,
)
from src.keyboards import get_donate_keyboard


def _render_donation_alert(
    *,
    display_name: str,
    amount_kopecks: int,
    comment: str | None,
    rank: int | None,
) -> str:
    lines = [
        '💰 <b>Новый донат!</b>',
        '',
        f'{escape_html(display_name)} задонатил <b>{format_amount(amount_kopecks)} ₽</b>',
    ]
    if rank is not None:
        lines.append(f'🏅 Место в рейтинге: <b>{rank}</b>')
    if comment:
        lines.append('')
        lines.append(f'💬 «{escape_html(comment)}»')
    return '\n'.join(lines)


class NotificationQueueService:
    def __init__(self, bot: Bot, redis: Redis) -> None:
        self.bot = bot
        self.redis = redis

    async def push(self, payload: DonationPayload, rank: int | None, is_anonymous: bool) -> None:
        data = json.dumps(
            {
                'payload': payload.model_dump(mode='json'),
                'rank': rank,
                'is_anonymous': is_anonymous,
            }
        )
        await self.redis.rpush(NOTIFICATION_QUEUE_KEY, data)
        logger.debug('Queued alert: amount={}', payload.amount)

    async def run_worker(self) -> None:
        logger.info('Notification worker started')
        while True:
            try:
                result = await self.redis.blpop(NOTIFICATION_QUEUE_KEY, timeout=0)
                if result:
                    _, raw = result
                    await self._process_one(raw)
            except asyncio.CancelledError:
                logger.info('Notification worker stopped')
                return
            except Exception:  # noqa: BLE001
                logger.exception('Notification worker error')

    async def _process_one(self, raw: bytes) -> None:
        msg = json.loads(raw)
        payload = DonationPayload.model_validate(msg['payload'])
        rank: int | None = msg.get('rank')
        is_anonymous: bool = msg.get('is_anonymous', False)

        if is_anonymous or not payload.telegram_user_id:
            display_name = 'Аноним'
        else:
            username, full_name = await get_user_display_name(
                self.bot, env.tribute.alert_group_id, payload.telegram_user_id
            )
            display_name = full_name or (f'@{username}' if username else 'Аноним')

        text = _render_donation_alert(
            display_name=display_name,
            amount_kopecks=payload.amount,
            comment=payload.message,
            rank=rank,
        )

        markup = get_donate_keyboard(env.tribute.donate_link)

        for attempt in range(3):
            try:
                await self.bot.send_message(
                    chat_id=env.tribute.alert_group_id,
                    message_thread_id=env.tribute.alert_topic_id,
                    text=text,
                    reply_markup=markup,
                )
            except TelegramRetryAfter as e:
                if attempt == 2:
                    raise
                logger.warning('Flood control, retry in {}s', e.retry_after)
                await asyncio.sleep(e.retry_after)
            else:
                logger.info('Donation alert sent')
                return
```

- [ ] **Step 2: Commit**

```bash
git add src/services/notification_queue.py
git commit -m "feat(services): notification queue + worker"
```

### Task 21: DonationService

**Files:**
- Create: `src/services/donation.py`

- [ ] **Step 1: Содержимое**

```python
from aiogram import Bot
from loguru import logger

from src.api.types import DonationPayload
from src.common import env, get_user_display_name
from src.database import DonationRepository, async_session


class DonationService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def save(self, payload: DonationPayload) -> tuple[bool, int | None, bool]:
        """
        Returns (saved_now, rank, is_anonymous).
        saved_now=False означает дубликат (идемпотентность).
        """
        is_anonymous = payload.anonymously or not payload.telegram_user_id

        username = None
        full_name = None
        if payload.telegram_user_id and not is_anonymous:
            username, full_name = await get_user_display_name(
                self.bot, env.tribute.alert_group_id, payload.telegram_user_id
            )

        async with async_session() as session:
            repo = DonationRepository(session)
            saved = await repo.add_donation(
                tribute_donation_request_id=payload.donation_request_id,
                amount=payload.amount,
                currency=payload.currency.lower(),
                telegram_user_id=payload.telegram_user_id,
                username=username,
                full_name=full_name,
                comment=payload.message,
                is_anonymous=is_anonymous,
            )

            if saved is None:
                logger.info(
                    'Duplicate webhook ignored: donation_request_id={}',
                    payload.donation_request_id,
                )
                return False, None, is_anonymous

            logger.info(
                'Donation saved: id={}, amount={}, anon={}',
                saved.id,
                payload.amount,
                is_anonymous,
            )

            if is_anonymous or not payload.telegram_user_id:
                return True, None, is_anonymous

            rank = await repo.get_user_rank(payload.telegram_user_id)
            return True, rank, is_anonymous
```

- [ ] **Step 2: Commit**

```bash
git add src/services/donation.py
git commit -m "feat(services): DonationService with idempotency"
```

### Task 22: FundraiserService

**Files:**
- Create: `src/services/fundraiser.py`

- [ ] **Step 1: Содержимое**

```python
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from src.common import (
    MOSCOW_TZ,
    calc_progress,
    env,
    escape_html,
    format_amount,
    format_date_moscow,
)
from src.database import Fundraiser, FundraiserRepository, FundraiserStatus, async_session
from src.keyboards import get_donate_keyboard


def render_progress_message(f: Fundraiser) -> str:
    percent, bar = calc_progress(f.current_amount, f.target_amount)
    lines = [
        '📹 <b>{}</b>'.format(escape_html(f.title or 'Сбор')),
        '',
        f'{bar} <b>{percent}%</b>',
        f'{format_amount(f.current_amount)} ₽ / {format_amount(f.target_amount)} ₽',
        '',
        f'📅 {format_date_moscow(f.start_date)} — {format_date_moscow(f.end_date)}',
    ]
    return '\n'.join(lines)


def render_completed_message(f: Fundraiser) -> str:
    percent, bar = calc_progress(f.current_amount, f.target_amount)
    return (
        '🎉 <b>Сбор завершён!</b>\n\n'
        f'<b>{escape_html(f.title or "")}</b>\n'
        f'{bar} <b>{percent}%</b>\n'
        f'Собрано: <b>{format_amount(f.current_amount)} ₽</b> из {format_amount(f.target_amount)} ₽\n\n'
        'Спасибо всем, кто участвовал!'
    )


class FundraiserService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def create_and_publish(
        self,
        *,
        target_amount: int,
        start_date: datetime,
        end_date: datetime,
        count_donations_from: datetime,
        title: str | None = None,
    ) -> Fundraiser:
        async with async_session() as session:
            repo = FundraiserRepository(session)
            initial = await repo.get_donations_sum_from_date(count_donations_from)

            f = await repo.create(
                target_amount=target_amount,
                start_date=start_date,
                end_date=end_date,
                count_donations_from=count_donations_from,
                title=title,
            )
            if initial > 0:
                await repo.update_amount(f.id, initial)
                f.current_amount = initial

        text = render_progress_message(f)
        msg = await self.bot.send_message(
            chat_id=env.tribute.alert_group_id,
            message_thread_id=env.tribute.fundraiser_topic_id,
            text=text,
            reply_markup=get_donate_keyboard(env.tribute.donate_link),
        )
        await self.bot.pin_chat_message(
            chat_id=env.tribute.alert_group_id,
            message_id=msg.message_id,
            disable_notification=True,
        )

        async with async_session() as session:
            repo = FundraiserRepository(session)
            f = await repo.set_message_id(f.id, msg.message_id)

        logger.info('Fundraiser published: id={}, message_id={}', f.id, msg.message_id)
        return f

    async def update_progress(self, amount: int) -> None:
        async with async_session() as session:
            repo = FundraiserRepository(session)
            f = await repo.get_active()
            if not f:
                return

            f = await repo.add_amount(f.id, amount)
            if not f or not f.channel_message_id:
                return

            try:
                await self.bot.edit_message_text(
                    chat_id=env.tribute.alert_group_id,
                    message_id=f.channel_message_id,
                    text=render_progress_message(f),
                    reply_markup=get_donate_keyboard(env.tribute.donate_link),
                )
            except TelegramAPIError as e:
                logger.warning('Failed to update progress message: {}', e)

            if f.current_amount >= f.target_amount:
                await self.close_fundraiser(f.id, FundraiserStatus.COMPLETED)

    async def close_fundraiser(
        self,
        fundraiser_id: int,
        status: str = FundraiserStatus.COMPLETED,
    ) -> None:
        async with async_session() as session:
            repo = FundraiserRepository(session)
            f = await repo.close(fundraiser_id, status)
            if not f:
                return

            if f.channel_message_id:
                try:
                    await self.bot.edit_message_text(
                        chat_id=env.tribute.alert_group_id,
                        message_id=f.channel_message_id,
                        text=render_completed_message(f),
                    )
                    await self.bot.unpin_chat_message(
                        chat_id=env.tribute.alert_group_id,
                        message_id=f.channel_message_id,
                    )
                except TelegramAPIError as e:
                    logger.warning('Failed to close pinned message: {}', e)

            try:
                await self.bot.send_message(
                    chat_id=env.tribute.alert_group_id,
                    text=render_completed_message(f),
                )
            except TelegramAPIError as e:
                logger.warning('Failed to send completion message: {}', e)

            await self._notify_admins(f, status)
            logger.info('Fundraiser closed: id={}, status={}', fundraiser_id, status)

    async def _notify_admins(self, f: Fundraiser, status: str) -> None:
        if status == FundraiserStatus.COMPLETED and f.current_amount >= f.target_amount:
            reason = 'цель достигнута'
        elif status == FundraiserStatus.COMPLETED:
            reason = 'истёк срок'
        else:
            reason = 'закрыт вручную'

        text = (
            f'ℹ️ Сбор #{f.id} закрыт ({reason}).\n'
            f'Собрано: {format_amount(f.current_amount)} ₽ '
            f'из {format_amount(f.target_amount)} ₽'
        )
        for admin_id in env.admin.admin_ids:
            try:
                await self.bot.send_message(chat_id=admin_id, text=text)
            except TelegramAPIError as e:
                logger.warning('Failed to notify admin {}: {}', admin_id, e)

    async def check_and_close_expired(self) -> None:
        now = datetime.now(MOSCOW_TZ)
        async with async_session() as session:
            repo = FundraiserRepository(session)
            expired = await repo.get_expired_active(now)
            for f in expired:
                await self.close_fundraiser(f.id, FundraiserStatus.COMPLETED)
```

- [ ] **Step 2: Commit**

```bash
git add src/services/fundraiser.py
git commit -m "feat(services): FundraiserService with pin/update/close"
```

### Task 23: DigestService

**Files:**
- Create: `src/services/digest.py`

- [ ] **Step 1: Содержимое**

```python
from datetime import datetime, time, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from src.common import (
    MOSCOW_TZ,
    calc_progress,
    env,
    escape_html,
    format_amount,
    format_date_moscow,
)
from src.database import DonationRepository, FundraiserRepository, async_session


def _today_window() -> tuple[datetime, datetime]:
    now = datetime.now(MOSCOW_TZ)
    today_start = datetime.combine(now.date(), time.min, tzinfo=MOSCOW_TZ)
    today_end = today_start + timedelta(days=1)
    return today_start, today_end


def _format_top_donor(rank: int, d: dict) -> str:
    name = d.get('full_name') or (f'@{d["username"]}' if d.get('username') else 'без имени')
    return f'{rank}. {escape_html(name)} — {format_amount(d["total_amount"])} ₽'


def render_digest(today_stats: dict, fundraiser, top: list[dict]) -> str:
    today_start, _ = _today_window()
    lines = [
        f'📊 <b>Сводка за {format_date_moscow(today_start)}</b>',
        '',
        '<b>За сегодня:</b>',
        f'• Собрано: {format_amount(today_stats["total_amount"])} ₽',
        f'• Донатов: {today_stats["count"]}',
        f'• Уникальных: {today_stats["unique_donors"]}',
    ]

    if fundraiser:
        percent, bar = calc_progress(fundraiser.current_amount, fundraiser.target_amount)
        remaining = max(fundraiser.target_amount - fundraiser.current_amount, 0)
        lines += [
            '',
            '<b>Всего по сбору:</b>',
            f'• {format_amount(fundraiser.current_amount)} ₽ / {format_amount(fundraiser.target_amount)} ₽',
            f'• {bar} {percent}%',
            f'• Осталось: {format_amount(remaining)} ₽',
        ]

    if top:
        lines += ['', '<b>Топ-3:</b>']
        for i, donor in enumerate(top, 1):
            lines.append(_format_top_donor(i, donor))

    return '\n'.join(lines)


class DigestService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_daily(self) -> None:
        start, end = _today_window()
        async with async_session() as session:
            d_repo = DonationRepository(session)
            f_repo = FundraiserRepository(session)
            today_stats = await d_repo.get_stats_for_period(start=start, end=end)
            top = await d_repo.get_top_donors(limit=3)
            fundraiser = await f_repo.get_active()

        text = render_digest(today_stats, fundraiser, top)

        for admin_id in env.admin.admin_ids:
            try:
                await self.bot.send_message(chat_id=admin_id, text=text)
            except TelegramAPIError as e:
                logger.warning('Failed to DM admin {}: {}', admin_id, e)

        logger.info('Daily digest sent to {} admins', len(env.admin.admin_ids))
```

- [ ] **Step 2: Commit**

```bash
git add src/services/digest.py
git commit -m "feat(services): daily digest service"
```

### Task 24: SchedulerService

**Files:**
- Create: `src/services/scheduler.py`

- [ ] **Step 1: Содержимое**

```python
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from redis.asyncio import Redis

from src.common import MOSCOW_TZ, env

from .digest import DigestService
from .fundraiser import FundraiserService


async def _check_expired(bot: Bot) -> None:
    await FundraiserService(bot).check_and_close_expired()


async def _send_digest(bot: Bot) -> None:
    await DigestService(bot).send_daily()


class SchedulerService:
    def __init__(self, bot: Bot, redis: Redis) -> None:
        self.bot = bot
        self.redis = redis
        self.scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)

    async def start(self) -> None:
        self.scheduler.add_job(
            _check_expired,
            'interval',
            minutes=30,
            id='check_expired',
            replace_existing=True,
            args=[self.bot],
        )
        self.scheduler.add_job(
            _send_digest,
            'cron',
            hour=env.digest.hour,
            minute=0,
            id='daily_digest',
            replace_existing=True,
            args=[self.bot],
        )
        self.scheduler.start()
        logger.info('Scheduler started: digest at {}:00 MSK', env.digest.hour)

    def stop(self) -> None:
        self.scheduler.shutdown()
```

- [ ] **Step 2: Commit**

```bash
git add src/services/scheduler.py
git commit -m "feat(services): scheduler with digest + expired check"
```

### Task 25: CommandService

**Files:**
- Create: `src/services/command.py`

- [ ] **Step 1: Содержимое (адаптация из источника, без i18n)**

```python
from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
)


def get_admin_commands() -> list[BotCommand]:
    return [
        BotCommand(command='fundraiser_create', description='Создать сбор'),
        BotCommand(command='fundraiser_close', description='Закрыть текущий сбор'),
        BotCommand(command='donations_csv', description='Выгрузка донатов CSV'),
    ]


class CommandService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def set_commands_all_private_chats(self, commands: list[BotCommand]) -> None:
        await self.bot.set_my_commands(commands=commands, scope=BotCommandScopeAllPrivateChats())

    async def set_commands_for_admins(
        self, *, admin_ids: list[int], commands: list[BotCommand]
    ) -> None:
        for admin_id in admin_ids:
            await self.bot.set_my_commands(
                commands=commands, scope=BotCommandScopeChat(chat_id=admin_id)
            )

    async def delete_commands_all_private_chats(self) -> None:
        await self.bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())

    async def delete_commands_for_admins(self, admin_ids: list[int]) -> None:
        for admin_id in admin_ids:
            await self.bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=admin_id))
```

- [ ] **Step 2: `services/__init__.py`**

```python
from .command import CommandService, get_admin_commands
from .digest import DigestService
from .donation import DonationService
from .fundraiser import FundraiserService
from .notification_queue import NotificationQueueService
from .scheduler import SchedulerService

__all__ = [
    'CommandService',
    'DigestService',
    'DonationService',
    'FundraiserService',
    'NotificationQueueService',
    'SchedulerService',
    'get_admin_commands',
]
```

- [ ] **Step 3: Commit**

```bash
git add src/services/command.py src/services/__init__.py
git commit -m "feat(services): commands + service package"
```

### Task 26: Tribute webhook router

**Files:**
- Create: `src/api/routers/tribute.py`

- [ ] **Step 1: Содержимое**

```python
import json
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from loguru import logger

from src.common import TEST_TRIBUTE_WEBHOOK_RESPONSE, TRIBUTE_WEBHOOK_PATH
from src.services import (
    DonationService,
    FundraiserService,
    NotificationQueueService,
)

from ..dependencies import (
    get_donation_service,
    get_fundraiser_service,
    get_notification_queue,
    verify_tribute_body,
)
from ..enums import TributeRequestType
from ..utils import parse_tribute_request

router = APIRouter()


@router.post(TRIBUTE_WEBHOOK_PATH)
async def tribute_webhook(
    body: Annotated[bytes, Depends(verify_tribute_body)],
    donation_service: Annotated[DonationService, Depends(get_donation_service)],
    notification_queue: Annotated[NotificationQueueService, Depends(get_notification_queue)],
    fundraiser_service: Annotated[FundraiserService, Depends(get_fundraiser_service)],
) -> Response:
    data = json.loads(body)

    if data == TEST_TRIBUTE_WEBHOOK_RESPONSE:
        logger.info('Test webhook received')
        return Response(content='OK')

    parsed = parse_tribute_request(data)
    if not parsed:
        logger.warning('Invalid tribute payload: {}', data)
        return Response(content='Invalid', status_code=400)

    if parsed.name not in (TributeRequestType.NEW_DONATION, TributeRequestType.RECURRENT_DONATION):
        logger.info('Skipping event: {}', parsed.name)
        return Response(content='OK')

    if parsed.payload.currency.lower() != 'rub':
        logger.warning('Non-RUB currency ignored: {}', parsed.payload.currency)
        return Response(content='OK')

    saved_now, rank, is_anonymous = await donation_service.save(parsed.payload)
    if not saved_now:
        return Response(content='OK')

    await notification_queue.push(parsed.payload, rank, is_anonymous)
    await fundraiser_service.update_progress(parsed.payload.amount)

    return Response(content='OK')
```

- [ ] **Step 2: Commit**

```bash
git add src/api/routers/tribute.py
git commit -m "feat(api): tribute webhook router"
```

### Task 27: Telegram webhook router

**Files:**
- Create: `src/api/routers/telegram.py`, `src/api/routers/__init__.py`, `src/api/__init__.py`

- [ ] **Step 1: `routers/telegram.py`**

```python
from typing import Annotated

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Depends, Request, Response
from loguru import logger

from src.common import BOT_WEBHOOK_PATH

from ..dependencies import get_bot, get_dispatcher, verify_telegram_secret

router = APIRouter()


@router.post(BOT_WEBHOOK_PATH, dependencies=[Depends(verify_telegram_secret)])
async def telegram_webhook(
    request: Request,
    bot: Annotated[Bot, Depends(get_bot)],
    dispatcher: Annotated[Dispatcher, Depends(get_dispatcher)],
) -> Response:
    data = await request.json()
    try:
        update = Update.model_validate(data, context={'bot': bot})
        await dispatcher.feed_update(bot, update)
    except Exception:  # noqa: BLE001
        logger.exception('Failed to feed update')
    return Response(content='OK')
```

- [ ] **Step 2: `routers/__init__.py`**

```python
from . import telegram, tribute

__all__ = ['telegram', 'tribute']
```

- [ ] **Step 3: `api/__init__.py`**

```python
from .types import DonationPayload, TributeRequest

__all__ = ['DonationPayload', 'TributeRequest']
```

- [ ] **Step 4: Commit**

```bash
git add src/api/routers/ src/api/__init__.py
git commit -m "feat(api): telegram webhook router + api package"
```

---

## Phase 5: aiogram bot

### Task 28: Filters

**Files:**
- Create: `src/filters/is_admin.py`, `is_private.py`, `is_alert_group.py`, `__init__.py`

- [ ] **Step 1: `is_admin.py`**

```python
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from src.common import env


class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return bool(user and user.id in env.admin.admin_ids)
```

- [ ] **Step 2: `is_private.py`**

```python
from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import Message


class IsPrivate(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type == ChatType.PRIVATE
```

- [ ] **Step 3: `is_alert_group.py`**

```python
from aiogram.filters import Filter
from aiogram.types import Message

from src.common import env


class IsAlertGroup(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.id == env.tribute.alert_group_id
```

- [ ] **Step 4: `__init__.py`**

```python
from .is_admin import IsAdmin
from .is_alert_group import IsAlertGroup
from .is_private import IsPrivate

__all__ = ['IsAdmin', 'IsAlertGroup', 'IsPrivate']
```

- [ ] **Step 5: Commit**

```bash
git add src/filters/
git commit -m "feat(filters): admin, private, alert_group"
```

### Task 29: Throttling middleware

**Files:**
- Create: `src/middlewares/throttling.py`, `src/middlewares/__init__.py`

- [ ] **Step 1: Содержимое (упрощённый аналог)**

```python
import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    """Один запрос в 0.5 сек на пользователя."""

    def __init__(self, rate: float = 0.5) -> None:
        self.rate = rate
        self._last: dict[int, float] = {}
        self._lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id
            async with self._lock:
                now = time.monotonic()
                last = self._last.get(user_id, 0)
                if now - last < self.rate:
                    return None
                self._last[user_id] = now
        return await handler(event, data)
```

- [ ] **Step 2: `__init__.py`**

```python
from .throttling import ThrottlingMiddleware

__all__ = ['ThrottlingMiddleware']
```

- [ ] **Step 3: Commit**

```bash
git add src/middlewares/
git commit -m "feat(middlewares): throttling"
```

### Task 30: Donate keyboard

**Files:**
- Create: `src/keyboards/inline/donate.py`, `src/keyboards/inline/__init__.py`, `src/keyboards/__init__.py`

- [ ] **Step 1: `donate.py`**

```python
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_donate_keyboard(donate_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='💳 Поддержать', url=donate_link)]]
    )
```

- [ ] **Step 2: `inline/__init__.py`**

```python
from .donate import get_donate_keyboard

__all__ = ['get_donate_keyboard']
```

- [ ] **Step 3: `keyboards/__init__.py`**

```python
from .inline import get_donate_keyboard

__all__ = ['get_donate_keyboard']
```

- [ ] **Step 4: Commit**

```bash
git add src/keyboards/
git commit -m "feat(keyboards): donate keyboard"
```

### Task 31: /start command (private)

**Files:**
- Create: `src/routers/private/messages/start.py`, `src/routers/private/__init__.py`, `src/routers/private/messages/__init__.py`

- [ ] **Step 1: `start.py`**

```python
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.common import env, escape_html
from src.filters import IsPrivate
from src.keyboards import get_donate_keyboard

router = Router()
router.message.filter(IsPrivate())


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        f'Привет, {escape_html(message.from_user.full_name)}!\n\n'
        '🏠 Мы собираем деньги на установку видеонаблюдения '
        f'на этажах нашего корпуса. Цель — <b>{env.fundraiser.title}</b>.\n\n'
        'Жми кнопку ниже чтобы поддержать сбор.'
    )
    await message.answer(text, reply_markup=get_donate_keyboard(env.tribute.donate_link))
```

- [ ] **Step 2: `messages/__init__.py`**

```python
from . import start

__all__ = ['start']
```

- [ ] **Step 3: `private/__init__.py`**

```python
from aiogram import Router

from .messages import start


def get_private_router() -> Router:
    router = Router(name='private')
    router.include_router(start.router)
    return router
```

- [ ] **Step 4: Commit**

```bash
git add src/routers/private/
git commit -m "feat(routers): /start command"
```

### Task 32: /stats command (group)

**Files:**
- Create: `src/routers/group/messages/stats.py`, `src/routers/group/__init__.py`, `src/routers/group/messages/__init__.py`

- [ ] **Step 1: `stats.py`**

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.common import env
from src.database import FundraiserRepository, async_session
from src.filters import IsAlertGroup
from src.keyboards import get_donate_keyboard
from src.services.fundraiser import render_progress_message

router = Router()
router.message.filter(IsAlertGroup())


@router.message(Command('stats'))
async def cmd_stats(message: Message) -> None:
    async with async_session() as session:
        f = await FundraiserRepository(session).get_active()

    if not f:
        await message.reply('Активных сборов нет.')
        return

    await message.reply(
        render_progress_message(f),
        reply_markup=get_donate_keyboard(env.tribute.donate_link),
    )
```

- [ ] **Step 2: `messages/__init__.py`**

```python
from . import stats

__all__ = ['stats']
```

- [ ] **Step 3: `group/__init__.py`**

```python
from aiogram import Router

from .messages import stats


def get_group_router() -> Router:
    router = Router(name='group')
    router.include_router(stats.router)
    return router
```

- [ ] **Step 4: Commit**

```bash
git add src/routers/group/
git commit -m "feat(routers): /stats command in group"
```

### Task 33: Admin /fundraiser_create + /fundraiser_close

**Files:**
- Create: `src/routers/admin/fundraiser.py`, `src/routers/admin/__init__.py`

- [ ] **Step 1: `fundraiser.py`**

```python
from datetime import datetime, time, timedelta

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from src.common import MOSCOW_TZ, env, format_amount, parse_date_msk
from src.database import FundraiserRepository, FundraiserStatus, async_session
from src.filters import IsAdmin, IsPrivate
from src.services import FundraiserService

router = Router()
router.message.filter(IsPrivate(), IsAdmin())


@router.message(Command('fundraiser_create'))
async def cmd_create(message: Message, command: CommandObject, bot: Bot) -> None:
    """
    Использование: /fundraiser_create [end_date]
    end_date в формате DD.MM.YYYY (опц., default = +30 дней).
    Цель и название берутся из env (FUNDRAISER__TARGET, FUNDRAISER__TITLE).
    """
    async with async_session() as session:
        existing = await FundraiserRepository(session).get_active()
        if existing:
            await message.answer(
                f'Уже есть активный сбор #{existing.id}. Сначала закрой его (/fundraiser_close).'
            )
            return

    now = datetime.now(MOSCOW_TZ)
    if command.args:
        end_date = parse_date_msk(command.args.strip())
        if not end_date:
            await message.answer('Не понял дату. Формат: DD.MM.YYYY')
            return
        end_date = datetime.combine(end_date.date(), time(23, 59), tzinfo=MOSCOW_TZ)
    else:
        end_date = now + timedelta(days=30)

    service = FundraiserService(bot)
    f = await service.create_and_publish(
        target_amount=env.fundraiser.target,
        start_date=now,
        end_date=end_date,
        count_donations_from=now,
        title=env.fundraiser.title,
    )
    await message.answer(
        f'✅ Сбор #{f.id} создан\n'
        f'Цель: {format_amount(f.target_amount)} ₽\n'
        f'Окончание: {end_date.strftime("%d.%m.%Y")}'
    )


@router.message(Command('fundraiser_close'))
async def cmd_close(message: Message, bot: Bot) -> None:
    async with async_session() as session:
        f = await FundraiserRepository(session).get_active()
        if not f:
            await message.answer('Активных сборов нет.')
            return

    service = FundraiserService(bot)
    await service.close_fundraiser(f.id, FundraiserStatus.CANCELLED)
    await message.answer(f'✅ Сбор #{f.id} закрыт.')
```

- [ ] **Step 2: Commit**

```bash
git add src/routers/admin/fundraiser.py
git commit -m "feat(routers): admin fundraiser commands"
```

### Task 34: Admin /donations_csv

**Files:**
- Create: `src/routers/admin/export.py`

- [ ] **Step 1: Содержимое**

```python
import csv
import io
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from src.common import format_amount
from src.database import DonationRepository, async_session
from src.filters import IsAdmin, IsPrivate

router = Router()
router.message.filter(IsPrivate(), IsAdmin())


@router.message(Command('donations_csv'))
async def cmd_export(message: Message) -> None:
    async with async_session() as session:
        donations = await DonationRepository(session).get_all()

    if not donations:
        await message.answer('Донатов пока нет.')
        return

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        'id', 'created_at', 'tribute_donation_request_id',
        'telegram_user_id', 'username', 'full_name',
        'amount_rub', 'currency', 'comment', 'is_anonymous',
    ])
    for d in donations:
        writer.writerow([
            d.id,
            d.created_at.isoformat(),
            d.tribute_donation_request_id,
            d.telegram_user_id or '',
            d.username or '',
            d.full_name or '',
            format_amount(d.amount),
            d.currency,
            (d.comment or '').replace('\n', ' '),
            d.is_anonymous,
        ])

    payload = buf.getvalue().encode('utf-8-sig')
    filename = f'donations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    await message.answer_document(BufferedInputFile(payload, filename=filename))
```

- [ ] **Step 2: `admin/__init__.py`**

```python
from aiogram import Router

from . import export, fundraiser


def get_admin_router() -> Router:
    router = Router(name='admin')
    router.include_router(fundraiser.router)
    router.include_router(export.router)
    return router
```

- [ ] **Step 3: Commit**

```bash
git add src/routers/admin/
git commit -m "feat(routers): admin /donations_csv export"
```

### Task 35: include_routers + routers/__init__.py

**Files:**
- Create: `src/routers/__init__.py`

- [ ] **Step 1: Содержимое**

```python
from aiogram import Dispatcher

from .admin import get_admin_router
from .group import get_group_router
from .private import get_private_router


def include_routers(dispatcher: Dispatcher) -> None:
    dispatcher.include_router(get_admin_router())
    dispatcher.include_router(get_private_router())
    dispatcher.include_router(get_group_router())
```

- [ ] **Step 2: Commit**

```bash
git add src/routers/__init__.py
git commit -m "feat(routers): aggregate routers"
```

---

## Phase 6: Wiring (main.py)

### Task 36: main.py

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: Содержимое**

```python
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from fastapi import FastAPI
from granian import Granian
from granian.constants import Interfaces
from loguru import logger
from redis.asyncio import Redis

from src.__meta__ import __app_name__, __version__
from src.api.routers import telegram, tribute
from src.common import (
    BOT_PRIVATE_COMMANDS,
    env,
    setup_logging,
)
from src.middlewares import ThrottlingMiddleware
from src.routers import include_routers
from src.services import (
    CommandService,
    NotificationQueueService,
    SchedulerService,
    get_admin_commands,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    bot = Bot(
        token=env.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    redis = Redis.from_url(env.redis.dsn)
    storage = RedisStorage(redis, key_builder=DefaultKeyBuilder(with_destiny=True))
    dispatcher = Dispatcher(storage=storage, bot=bot, redis=redis)

    throttling = ThrottlingMiddleware()
    dispatcher.message.outer_middleware(throttling)
    dispatcher.callback_query.outer_middleware(throttling)

    include_routers(dispatcher)

    app.state.bot = bot
    app.state.redis = redis
    app.state.dispatcher = dispatcher

    cmd_service = CommandService(bot)
    await cmd_service.set_commands_all_private_chats(BOT_PRIVATE_COMMANDS)
    await cmd_service.set_commands_for_admins(
        admin_ids=env.admin.admin_ids,
        commands=[*BOT_PRIVATE_COMMANDS, *get_admin_commands()],
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(
        url=env.app.webhook_url,
        secret_token=env.app.secret_token.get_secret_value(),
        allowed_updates=dispatcher.resolve_used_update_types(),
        drop_pending_updates=True,
    )

    notification_queue = NotificationQueueService(bot, redis)
    app.state.notification_queue = notification_queue
    worker_task = asyncio.create_task(notification_queue.run_worker())

    scheduler_service = SchedulerService(bot, redis)
    await scheduler_service.start()

    logger.info('{} v{} started', __app_name__, __version__)

    try:
        yield
    finally:
        worker_task.cancel()
        await asyncio.gather(worker_task, return_exceptions=True)
        scheduler_service.stop()
        await cmd_service.delete_commands_all_private_chats()
        await cmd_service.delete_commands_for_admins(env.admin.admin_ids)
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.fsm.storage.close()
        await redis.aclose()
        await bot.session.close()
        logger.info('Bot shutdown')


setup_logging(debug=env.app.debug)

app = FastAPI(lifespan=lifespan)
app.include_router(telegram.router)
app.include_router(tribute.router)


def main() -> None:
    server = Granian(
        target='src.main:app',
        address=env.app.host,
        port=env.app.port,
        interface=Interfaces.ASGI,
    )
    server.serve()


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Commit**

```bash
git add src/main.py
git commit -m "feat: main.py with FastAPI lifespan"
```

---

## Phase 7: Tests

### Task 37: pytest fixtures

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Содержимое**

```python
import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from testcontainers.postgres import PostgresContainer

import src.database.models  # noqa: F401  - регистрация моделей


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def postgres_container() -> PostgresContainer:
    with PostgresContainer('postgres:16-alpine', driver='asyncpg') as pg:
        yield pg


@pytest_asyncio.fixture(scope='session')
async def engine(postgres_container):
    eng = create_async_engine(postgres_container.get_connection_url(), echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncIterator[AsyncSession]:
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session
        for table in reversed(SQLModel.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()
```

- [ ] **Step 2: Commit**

```bash
git add tests/conftest.py
git commit -m "test: fixtures with testcontainers Postgres"
```

### Task 38: Integration test — webhook saves donation

**Files:**
- Create: `tests/integration/test_donation_repo_integration.py`

- [ ] **Step 1: Содержимое**

```python
import pytest

from src.database.repositories.donation import DonationRepository


@pytest.mark.asyncio
async def test_add_donation_returns_record(db_session):
    repo = DonationRepository(db_session)
    d = await repo.add_donation(
        tribute_donation_request_id=42,
        amount=200000,
        telegram_user_id=999,
        username='alice',
        full_name='Alice Wonderland',
        comment='удачи',
    )
    assert d is not None
    assert d.amount == 200000
    assert d.username == 'alice'


@pytest.mark.asyncio
async def test_add_donation_idempotent(db_session):
    repo = DonationRepository(db_session)
    first = await repo.add_donation(tribute_donation_request_id=43, amount=100000)
    second = await repo.add_donation(tribute_donation_request_id=43, amount=999999)
    assert first is not None
    assert second is None  # дубликат отброшен


@pytest.mark.asyncio
async def test_user_rank_two_donors(db_session):
    repo = DonationRepository(db_session)
    await repo.add_donation(tribute_donation_request_id=1, amount=300000, telegram_user_id=1)
    await repo.add_donation(tribute_donation_request_id=2, amount=100000, telegram_user_id=2)

    assert await repo.get_user_rank(1) == 1
    assert await repo.get_user_rank(2) == 2
    assert await repo.get_user_rank(404) is None


@pytest.mark.asyncio
async def test_get_top_donors_excludes_anonymous(db_session):
    repo = DonationRepository(db_session)
    await repo.add_donation(tribute_donation_request_id=10, amount=500000, telegram_user_id=1, username='top')
    await repo.add_donation(tribute_donation_request_id=11, amount=999999, is_anonymous=True)
    top = await repo.get_top_donors(limit=10)
    assert len(top) == 1
    assert top[0]['username'] == 'top'
```

- [ ] **Step 2: Run tests**

```bash
uv run pytest tests/integration/ -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_donation_repo_integration.py
git commit -m "test(integration): donation repository idempotency + rank"
```

### Task 39: E2E test — full webhook flow

**Files:**
- Create: `tests/e2e/test_webhook_flow.py`

- [ ] **Step 1: Содержимое**

```python
import hashlib
import hmac
import json
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.routers import tribute as tribute_router
from src.api.utils.parser import parse_tribute_request


def _signed_body(secret: str, data: dict) -> tuple[bytes, str]:
    body = json.dumps(data).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return body, sig


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_signature(monkeypatch, db_session):
    from fastapi import FastAPI

    monkeypatch.setattr('src.common.env.tribute.api_key.get_secret_value', lambda: 'secret')

    app = FastAPI()
    app.include_router(tribute_router.router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        body, _ = _signed_body('wrong-secret', {'name': 'new_donation', 'payload': {}})
        resp = await client.post('/tribute', content=body, headers={'trbt-signature': 'deadbeef'})
        assert resp.status_code == 401


def test_parse_tribute_request_round_trip():
    """Smoke: парсер работает на реалистичном payload."""
    data = {
        'name': 'new_donation',
        'created_at': '2026-05-07T12:00:00Z',
        'sent_at': '2026-05-07T12:00:01Z',
        'payload': {
            'donation_request_id': 100,
            'donation_name': 'Камеры',
            'message': 'привет',
            'period': '',
            'amount': 200000,
            'currency': 'rub',
            'anonymously': False,
            'web_app_link': '',
            'telegram_user_id': 555,
        },
    }
    parsed = parse_tribute_request(data)
    assert parsed is not None
    assert parsed.payload.message == 'привет'
```

- [ ] **Step 2: Run**

```bash
uv run pytest tests/e2e/ -v
```

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/test_webhook_flow.py
git commit -m "test(e2e): webhook signature + payload parsing smoke"
```

### Task 40: Coverage check

- [ ] **Step 1: Запустить с coverage**

```bash
uv run pytest --cov=src --cov-report=term-missing
```

Expected: ≥80% покрытия. Если ниже — добавить юнит-тестов на пробельные модули (digest service, fundraiser render, formatting).

- [ ] **Step 2: Если не хватает покрытия — добавить тесты**

Создать `tests/unit/test_formatting.py`:

```python
from src.common import calc_progress, format_amount


def test_format_amount_integer():
    assert format_amount(100000) == '1 000'


def test_format_amount_thousand_separator():
    assert format_amount(69800000) == '698 000'


def test_format_amount_fractional():
    assert format_amount(100050) == '1 000.5'


def test_calc_progress_zero():
    p, bar = calc_progress(0, 1000)
    assert p == 0
    assert '▱' * 10 in bar


def test_calc_progress_full():
    p, bar = calc_progress(1000, 1000)
    assert p == 100
    assert '▰' * 10 in bar


def test_calc_progress_overflow():
    p, _ = calc_progress(2000, 1000)
    assert p == 100


def test_calc_progress_zero_target():
    p, _ = calc_progress(50, 0)
    assert p == 0
```

Создать `tests/unit/test_digest.py`:

```python
from datetime import datetime
from unittest.mock import MagicMock

from src.common import MOSCOW_TZ
from src.services.digest import render_digest


def test_render_digest_no_fundraiser_no_top():
    today = {'total_amount': 0, 'count': 0, 'unique_donors': 0}
    text = render_digest(today, None, [])
    assert '📊' in text
    assert 'Собрано: 0 ₽' in text


def test_render_digest_with_fundraiser_and_top():
    today = {'total_amount': 200000, 'count': 1, 'unique_donors': 1}
    fundraiser = MagicMock()
    fundraiser.current_amount = 200000
    fundraiser.target_amount = 1000000
    top = [
        {'telegram_user_id': 1, 'username': 'a', 'full_name': 'Alice', 'total_amount': 200000},
    ]
    text = render_digest(today, fundraiser, top)
    assert 'Топ-3' in text
    assert 'Alice' in text
    assert '20%' in text
```

- [ ] **Step 3: Запустить ещё раз**

```bash
uv run pytest --cov=src --cov-report=term-missing
```

- [ ] **Step 4: Commit**

```bash
git add tests/unit/test_formatting.py tests/unit/test_digest.py
git commit -m "test(unit): formatting + digest rendering"
```

---

## Phase 8: Документация и финал

### Task 41: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Содержимое**

````markdown
# Camera Fundraiser Telegram Bot

Бот для сбора донатов через Tribute на установку видеонаблюдения в подъезде.

## Возможности

- Приём вебхуков Tribute с HMAC-проверкой
- Запись каждого доната в Postgres с полной информацией (кто, сумма, комментарий)
- Алерты в группу жильцов в выделенный топик
- Автообновляемый закреп с прогрессом сбора
- По достижении цели — уведомление в общий чат + DM админам
- Ежедневная сводка админам
- Команды `/start`, `/stats`, `/fundraiser_create`, `/fundraiser_close`, `/donations_csv`

## Стек

Python 3.13, FastAPI + Granian, aiogram 3, SQLModel + asyncpg, Redis, Alembic, APScheduler.

## Запуск локально

1. Скопировать `.env.example` в `.env` и заполнить.
2. Поднять postgres + redis:
   ```bash
   docker compose -f docker-compose.local.yml up -d
   ```
3. Применить миграции:
   ```bash
   uv run alembic upgrade head
   ```
4. Запустить бота:
   ```bash
   uv run python -m src.main
   ```

## Деплой (production)

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Tribute шлёт вебхук на `https://${APP__DOMAIN}/tribute`. Telegram — на `https://${APP__DOMAIN}/telegram`.

## Тесты

```bash
make test
```

≥80% покрытия по `src/`.
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README with setup and deploy"
```

### Task 42: Финальная проверка

- [ ] **Step 1: Линтер**

```bash
uv run ruff check src tests
uv run ruff format --check src tests
```

- [ ] **Step 2: Тесты с coverage**

```bash
uv run pytest --cov=src --cov-report=term-missing
```

- [ ] **Step 3: Локальный запуск (smoke)**

```bash
docker compose -f docker-compose.local.yml up -d
uv run alembic upgrade head
uv run python -m src.main &
sleep 5
curl -X POST http://localhost:9090/tribute -d '{"test_event":"test_event"}' -i
# должен вернуть 401 (нет подписи)
kill %1
```

- [ ] **Step 4: Финальный commit (если что-то поправили)**

```bash
git status
# если есть изменения:
git add -A
git commit -m "chore: lint and final cleanup"
```

---

## Self-review

**Spec coverage:**
- ✅ Tribute webhook + HMAC — Task 17, 19, 26
- ✅ Расширенная схема Donation — Task 10, 13
- ✅ Идемпотентность — Task 13 (ON CONFLICT), Task 38 (тест)
- ✅ Алерт в alert_topic_id — Task 20
- ✅ Закреп прогресса в fundraiser_topic_id — Task 22
- ✅ Сообщение в общий чат при закрытии — Task 22 (`close_fundraiser`)
- ✅ DM админам — Task 22, 23
- ✅ Дейли-сводка — Task 23, 24
- ✅ /start, /stats — Task 31, 32
- ✅ Админ-команды + CSV экспорт — Task 33, 34
- ✅ Тесты unit/integration/e2e — Task 17, 18, 38, 39, 40

**Placeholder scan:** В коде нет TBD/TODO. Все функции имеют реализацию.

**Type consistency:**
- `add_donation` сигнатура одна и та же (Task 13, используется в Task 21)
- `render_progress_message` определена в Task 22, используется в Task 32
- `render_digest` определена в Task 23, используется в Task 24 (через `DigestService.send_daily`)

---

## Verification

После выполнения всех тасок:
- `make lint` — чисто
- `make test` — зелёный, ≥80% покрытие
- `docker compose -f docker-compose.local.yml up -d` — postgres + redis в норме
- `alembic upgrade head` — миграции применились
- POST `/tribute` без подписи → 401
- POST `/tribute` с правильной подписью и payload → 200, запись в БД, сообщение в группу (на тестовом чате)
- `/start` в личке → приветствие + кнопка
- `/stats` в группе → прогресс
- В установленный час дня → дейли-сводка приходит в личку админам
