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
