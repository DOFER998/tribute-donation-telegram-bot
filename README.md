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

На сервере держим:

- `docker-compose.prod.yml` + `.env` (бот + БД + редис)
- `caddy/docker-compose.yml` + `caddy/Caddyfile` + `caddy/.env` (reverse proxy с авто-TLS)

Стек разделён на две независимых compose-папки, общающихся через общую docker-сеть `proxy`.

### 1) Создаём общую сеть один раз

```bash
docker network create proxy
```

### 2) Поднимаем основной стек

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Бот сам прогоняет `alembic upgrade head` и запускает Granian. Контейнер не открывает наружу никаких портов — внешний трафик придёт через Caddy.

### 3) Поднимаем Caddy

```bash
cd caddy
cp .env.example .env       # заполнить DOMAIN и ACME_EMAIL
docker compose up -d
```

Caddy слушает 80/443, проксирует `https://${DOMAIN}/telegram` и `/tribute` в `bot:9090` через сеть `proxy`. Сертификат Let's Encrypt оформляется автоматически при первом запросе.

Tribute шлёт вебхук на `https://${DOMAIN}/tribute`, Telegram — на `https://${DOMAIN}/telegram`.

### Что в `.env` для прода

Минимум для бота:

- `BOT__TOKEN`
- `APP__DOMAIN`, `APP__SECRET_TOKEN`
- `POSTGRES__USER`, `POSTGRES__PASSWORD`, `POSTGRES__DATABASE`
- `REDIS__PASSWORD`
- `TRIBUTE__API_KEY`, `TRIBUTE__DONATE_LINK`, `TRIBUTE__ALERT_GROUP_ID`
- `ADMIN__IDS`

Минимум для Caddy (`caddy/.env`):

- `DOMAIN` — тот же что `APP__DOMAIN`
- `ACME_EMAIL` — для уведомлений Let's Encrypt

### Сборка образа в CI

`.github/workflows/docker-publish.yml` собирает и пушит образ в `ghcr.io/dofer998/tribute-donation-telegram-bot` при пуше в `main` и при тегах `v*`. Используется `GITHUB_TOKEN`.

## Тесты и проверки

```bash
make check        # ruff + ty + pytest
make test         # pytest с coverage
make typecheck    # ty (Astral type checker)
make lint         # ruff
```
