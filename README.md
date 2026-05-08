# Camera Fundraiser Telegram Bot

Бот для сбора донатов через Tribute на установку видеонаблюдения в подъезде.

## Возможности

- Приём вебхуков Tribute с HMAC-проверкой
- Запись каждого взноса в Postgres с полной информацией (кто, сумма, комментарий)
- Алерты в группу жильцов в топик сбора
- Автообновляемый закреп с прогрессом
- По достижении цели — уведомление + DM админам
- Ежедневное публичное напоминание (фото-баннер + прогресс)
- Единая админ-команда `/fundraiser` с интерактивным меню (создание/закрытие/CSV)
- FSM-флоу создания сбора через кнопки

## Стек

Python 3.13, FastAPI + Granian, aiogram 3, SQLModel + asyncpg, Redis, Alembic, APScheduler, Jinja2.

## Запуск локально

Для локального запуска `make run` бот стартует **вне** контейнера (host-машина), поэтому Postgres/Redis смотрят на `localhost`. В `.env` помимо обязательных значений заполни:

```
POSTGRES__HOST=localhost
REDIS__HOST=localhost
```

Шаги:

1. Скопировать `.env.example` → `.env`, заполнить.
2. Поднять postgres + redis: `make up`
3. Запустить бота: `make run` (миграции прогоняются автоматически)

## Деплой (production)

Прод запускается из готового образа из GHCR — клонировать код на сервер не нужно.

На сервере достаточно двух файлов:

1. `docker-compose.prod.yml`
2. `.env` (только секреты + per-deploy значения, см. `.env.example`)

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Образ при старте сам прогоняет `alembic upgrade head`, потом запускает Granian.

Tribute шлёт вебхук на `https://${APP__DOMAIN}/tribute`, Telegram — на `https://${APP__DOMAIN}/telegram`.

### Что в `.env` для прода

Только то, что нельзя угадать или что секретно:

- `BOT__TOKEN`
- `APP__DOMAIN`, `APP__SECRET_TOKEN`
- `POSTGRES__PASSWORD`, `REDIS__PASSWORD`
- `TRIBUTE__API_KEY`, `TRIBUTE__DONATE_LINK`, `TRIBUTE__ALERT_GROUP_ID`
- `ADMIN__IDS`

Хосты, порты, БД-имя, юзер, и пр. — захардкожены в `docker-compose.prod.yml` и/или дефолтны в pydantic-конфиге.

### Сборка образа в CI

`.github/workflows/docker-publish.yml` собирает и пушит образ в `ghcr.io/<owner>/<repo>` при пуше в `main` и при создании тегов `v*`. Никаких секретов не нужно — используется `GITHUB_TOKEN`.

Если ghcr-пакет приватный, после первого пуша зайти в Settings → Packages и сделать его публичным или дать read-доступ деплой-машине через PAT.

## Тесты и проверки

```bash
make check        # ruff + ty + pytest
make test         # pytest с coverage
make typecheck    # ty (Astral type checker)
make lint         # ruff
```
