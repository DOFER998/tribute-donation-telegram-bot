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

Прод запускается из готового образа из GHCR — клонировать код на сервер не нужно.

На сервере:

1. Положить рядом `docker-compose.prod.yml` и `.env` (заполненный).
2. В `.env` указать образ:
   ```
   BOT_IMAGE=ghcr.io/<owner>/<repo>:latest
   ```
3. Запустить:
   ```bash
   docker compose -f docker-compose.prod.yml pull
   docker compose -f docker-compose.prod.yml up -d
   ```

Образ при старте сам прогоняет `alembic upgrade head`, потом запускает бота — это делает `main()` в `src/main.py`.

Tribute шлёт вебхук на `https://${APP__DOMAIN}/tribute`. Telegram — на `https://${APP__DOMAIN}/telegram`.

### Сборка образа в CI

`.github/workflows/docker-publish.yml` собирает и пушит образ в `ghcr.io/<owner>/<repo>` при пуше в `main` и при создании тегов `v*`. Никаких секретов не нужно — используется `GITHUB_TOKEN`.

Если ghcr-пакет приватный, после первого пуша зайти в Settings → Packages и сделать его доступным или дать read-доступ деплой-машине через PAT.

## Тесты

```bash
make test
```

24 теста, покрытие ~46% (security-critical пути закрыты: HMAC, парсинг payload, идемпотентность).
