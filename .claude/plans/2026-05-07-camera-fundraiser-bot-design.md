# Camera Fundraiser Telegram Bot — Design Spec

**Дата:** 2026-05-07
**Проект:** `/Users/c0mrade/PycharmProjects/tribute-donation-telegram-bot`
**Источник модулей:** `/Users/c0mrade/PycharmProjects/tribute-bedolaga-telegram-bot`

## Контекст

Цель — собрать деньги жильцов первого корпуса жилого дома на установку системы видеонаблюдения (3 камеры на каждый из 24 этажей с выводом в консьержную). Общая сумма сбора — 698 000 ₽, по 2 000 ₽ с квартиры. Только первый корпус участвует. Платежи принимаются через Tribute (исключительно в рублях).

Бот должен:
- Принимать вебхуки Tribute о новых донатах
- Сохранять каждый донат в БД с полной информацией (кто, сумма, комментарий)
- Постить алерты о донатах в группу жильцов в выделенный топик
- Поддерживать закреплённое сообщение прогресса сбора в отдельном топике (как в исходнике)
- По достижении цели — закрывать сбор, постить уведомление в общий чат, слать DM админам
- Раз в сутки слать админам сводку по сбору в личку

## Стек

Полностью повторяет исходник:

- Python 3.13
- FastAPI + Granian (ASGI server)
- aiogram 3.x (Telegram Bot framework)
- SQLModel + asyncpg (Postgres)
- Redis (FSM storage + очередь алертов)
- Alembic (миграции)
- APScheduler (расписание)
- pydantic-settings (env-конфиг)
- loguru (логирование)
- pytz (Europe/Moscow)

Деплой: docker-compose с тремя сервисами — `bot`, `postgres`, `redis`.

## Структура проекта

```
src/
├── main.py                              # FastAPI lifespan, init bot/redis/scheduler
├── __meta__.py                          # __app_name__, __version__
├── api/
│   ├── routers/
│   │   ├── tribute.py                   # POST /tribute (Tribute webhook)
│   │   └── telegram.py                  # POST /telegram (aiogram webhook)
│   ├── utils/
│   │   ├── signature.py                 # HMAC-SHA256 verify (копия из источника)
│   │   └── parser.py                    # Pydantic parser для TributeRequest
│   ├── types/
│   │   ├── base.py                      # BaseObject (Pydantic config)
│   │   ├── tribute_request.py           # TributeRequest envelope
│   │   └── donation_payload.py          # DonationPayload
│   ├── enums/
│   │   └── tribute_request_type.py      # NEW_DONATION / RECURRENT_DONATION
│   └── dependencies.py                  # FastAPI DI: bot, redis, services
├── services/
│   ├── donation.py                      # save() + ранг донора + текст алерта
│   ├── notification_queue.py            # Redis-очередь + воркер
│   ├── fundraiser.py                    # закреп прогресса, авто-обновление, закрытие
│   ├── scheduler.py                     # APScheduler jobs
│   ├── command.py                       # установка bot commands
│   └── digest.py                        # формирование текста дейли-сводки
├── database/
│   ├── session.py                       # async_session, engine
│   ├── models/
│   │   ├── mixins.py                    # TimestampMixin
│   │   ├── donation.py                  # Donation (РАСШИРЕННАЯ)
│   │   └── fundraiser.py                # Fundraiser (копия)
│   └── repositories/
│       ├── donation.py
│       └── fundraiser.py
├── routers/                             # aiogram routers
│   ├── private/
│   │   └── messages/start.py            # /start
│   ├── group/
│   │   └── messages/stats.py            # /stats
│   └── admin/
│       ├── fundraiser.py                # /fundraiser_create, /fundraiser_close
│       └── export.py                    # /donations_csv
├── keyboards/
│   └── inline/donate.py                 # кнопка «Поддержать» с Tribute-ссылкой
├── filters/
│   ├── is_admin.py
│   ├── is_private.py
│   └── is_alert_group.py
├── middlewares/
│   └── throttling.py                    # антифлуд
└── common/
    ├── config/
    │   ├── environment.py               # Environment, env
    │   └── types/
    │       ├── base.py
    │       ├── bot.py
    │       ├── app.py
    │       ├── postgres.py
    │       ├── redis.py
    │       ├── tribute.py               # api_key, donate_link, alert_*, fundraiser_topic_id
    │       ├── fundraiser.py            # target, title
    │       ├── digest.py                # daily digest hour
    │       └── admin.py
    ├── constants.py                     # пути, MOSCOW_TZ, ключи Redis
    └── utils/
        ├── formatting.py                # format_amount, calc_progress
        ├── datetime.py                  # utc_now, format_date_moscow
        ├── logging.py                   # setup_logging
        └── telegram.py                  # get_user_by_id

alembic/                                 # миграции
├── env.py
├── script.py.mako
└── versions/
    └── 0001_initial.py                  # создание donations + fundraisers

tests/
├── conftest.py                          # fixtures (testcontainers postgres, fake bot)
├── unit/
│   ├── test_signature.py
│   ├── test_parser.py
│   ├── test_formatting.py
│   └── test_donation_service.py
├── integration/
│   ├── test_tribute_webhook.py          # webhook → DB
│   ├── test_idempotency.py              # повторный вебхук не дублирует
│   └── test_fundraiser_progress.py
└── e2e/
    └── test_donation_flow.py            # подписанный вебхук → DB + алерт (mock Bot)

docker-compose.local.yml
docker-compose.prod.yml
Dockerfile
alembic.ini
pyproject.toml
.env.example
README.md
```

## Схема БД

### `donations` (расширена относительно источника)

| Колонка | Тип | Constraints | Описание |
|--------|-----|-------------|----------|
| `id` | BigInt PK | autoincrement | |
| `tribute_donation_request_id` | BigInt | UNIQUE NOT NULL | идемпотентность Tribute-вебхука |
| `telegram_user_id` | BigInt | nullable, INDEX | id жильца в Telegram |
| `username` | varchar(64) | nullable | @username на момент доната |
| `full_name` | varchar(256) | nullable | имя из Telegram-профиля |
| `amount` | BigInt | NOT NULL | сумма в копейках |
| `currency` | varchar(3) | INDEX, default `'rub'` | для будущей расширяемости, но в коде хардкод |
| `comment` | text | nullable | сообщение от донатера (`message` из payload) |
| `is_anonymous` | bool | INDEX, default false | анонимный донат |
| `created_at` | timestamptz | INDEX, default now() | |
| `updated_at` | timestamptz | default now(), onupdate now() | |

### `fundraisers` (копия источника, без изменений)

| Колонка | Тип |
|--------|-----|
| `id` | BigInt PK |
| `title` | varchar nullable |
| `target_amount` | BigInt |
| `current_amount` | BigInt default 0 |
| `start_date` | timestamptz |
| `end_date` | timestamptz |
| `count_donations_from` | timestamptz |
| `channel_message_id` | BigInt nullable |
| `status` | varchar INDEX (`active`/`completed`/`cancelled`) |
| `created_at`, `updated_at` | timestamptz |

## Поток обработки доната

```
Tribute → POST /tribute с заголовком trbt-signature
  ↓
verify_tribute_body(): HMAC-SHA256(body, TRIBUTE__API_KEY) == header
  ↓
parse_tribute_request(): Pydantic → TributeRequest
  ↓ filter: name in {NEW_DONATION, RECURRENT_DONATION}
DonationService.save(payload):
  - INSERT INTO donations ... ON CONFLICT (tribute_donation_request_id) DO NOTHING
  - вернуть rank + is_anonymous
  ↓
NotificationQueueService.push(): RPUSH в Redis tribute:notifications
  ↓ (асинхронно, фоновый воркер)
Воркер:
  - BLPOP из очереди
  - resolve username через get_user_by_id (по chat_id)
  - bot.send_message(alert_group_id, message_thread_id=alert_topic_id, text=...)
FundraiserService.update_progress(amount):
  - UPDATE fundraisers SET current_amount = current_amount + amount WHERE status='active'
  - bot.edit_message_text(channel_message_id) — обновить закреп в fundraiser_topic_id
  - if current_amount >= target_amount → close_fundraiser()
close_fundraiser():
  - UPDATE status='completed'
  - правка закрепа на «сбор завершён»
  - unpin_chat_message
  - bot.send_message в общий чат: «Сбор завершён, спасибо!»
  - DM каждому admin_id: финальная сводка
```

## Идемпотентность

Tribute может ретраить вебхук при не-200 ответе. Защита:

```sql
INSERT INTO donations (tribute_donation_request_id, ...)
VALUES ($1, ...)
ON CONFLICT (tribute_donation_request_id) DO NOTHING
RETURNING id;
```

Если RETURNING пустой — донат уже сохранён, не делаем push в очередь и не обновляем fundraiser.

## Расписание (APScheduler, Europe/Moscow)

| Job ID | Триггер | Действие |
|--------|---------|----------|
| `check_expired_fundraisers` | interval 30 min | закрыть истёкшие активные сборы |
| `daily_digest` | cron: hour=DIGEST__HOUR, minute=0 | DM каждому admin_id со сводкой |

**Дейли-сводка содержит:**
- Заголовок «Сводка за DD.MM.YYYY»
- Собрано за сегодня: сумма + кол-во донатов + уникальных донатёров
- Собрано всего: сумма + % от цели + прогресс-бар
- Осталось до цели: сумма
- Топ-3 квартиры по сумме (если не анонимы)

## Команды

| Команда | Доступ | Действие |
|---------|--------|----------|
| `/start` | приват | Приветствие + кнопка «Поддержать» (Tribute-ссылка) |
| `/stats` | группа жильцов | Показать прогресс-бар + сумму |
| `/fundraiser_create <target> <end_date>` | админ DM | Создать активный сбор |
| `/fundraiser_close` | админ DM | Принудительно закрыть текущий сбор |
| `/donations_csv` | админ DM | Выгрузка всех донатов в CSV |

## Конфигурация (.env)

```ini
# Bot
BOT__TOKEN=<telegram-bot-token>

# App (FastAPI / Granian)
APP__DOMAIN=example.com
APP__HOST=0.0.0.0
APP__PORT=9090
APP__SECRET_TOKEN=<random-secret>
APP__DEBUG=false

# Postgres
POSTGRES__HOST=postgres
POSTGRES__PORT=5432
POSTGRES__USER=fundraiser
POSTGRES__PASSWORD=<password>
POSTGRES__DATABASE=fundraiser_bot

# Redis
REDIS__HOST=redis
REDIS__PORT=6379
REDIS__NAME=0
REDIS__PASSWORD=<password>

# Tribute
TRIBUTE__API_KEY=<hmac-secret>
TRIBUTE__DONATE_LINK=https://tribute.tg/...
TRIBUTE__ALERT_GROUP_ID=-1001234567890
TRIBUTE__ALERT_TOPIC_ID=2          # топик «Донаты»
TRIBUTE__FUNDRAISER_TOPIC_ID=3     # топик «Прогресс» (где висит закреп)

# Fundraiser
FUNDRAISER__TARGET=69800000        # 698 000 ₽ в копейках
FUNDRAISER__TITLE=Камеры для 1 корпуса

# Daily digest
DIGEST__HOUR=21                    # время (МСК) ежедневной сводки админам

# Admin
ADMIN__IDS=[123456789, 987654321]
```

## Что выпиливается из источника

- `i18n/`, `locales/`, `middlewares/i18n.py` (fluentogram) — все тексты прямо в коде на русском
- `dialogs/`, `aiogram-dialog` — не используется
- `services/leaderboard.py`, `keyboards/inline/leaderboard.py`, `routers/group/callbacks/leaderboard.py`, `callback_data/leaderboard.py` — лидерборд не нужен
- `routers/private/messages/broadcast.py`, `dialogs/broadcast.py`, `states/broadcast.py` — broadcast не нужен (пока)
- `services/scheduler.py::send_github_stars_reminder`, `keyboards/inline/github_stars.py`, `common/config/types/github.py` — github stars напоминалка
- `common/constants.py`: все `*_EMOJI_ID` константы (60+)
- `services/donation.py`: `_PHRASE_COUNTS`, `DonationTier`, `_get_amount_tier`, `_get_random_phrase` — фразочки-тиры (small/medium/large/cosmic)
- Мульти-валютная логика в `donation.py` репозитории — упрощается до RUB-only

## Что копируется 1-в-1 или с минимальной правкой

- `api/utils/signature.py` (HMAC verify)
- `api/utils/parser.py`
- `api/types/base.py`, `tribute_request.py`, `donation_payload.py`
- `api/enums/tribute_request_type.py`
- `database/models/fundraiser.py`, `mixins.py`
- `database/repositories/fundraiser.py`
- `database/session.py`
- `common/utils/formatting.py` (`format_amount`, `calc_progress`)
- `common/utils/datetime.py` (`utc_now`, `format_date_moscow`)
- `common/utils/logging.py`
- `common/config/types/base.py`, `bot.py`, `app.py`, `postgres.py`, `redis.py`, `admin.py`
- `filters/is_admin.py`, `is_private.py`, `is_alert_group.py`
- `middlewares/throttling.py`
- `services/command.py`
- структура `main.py` (lifespan, FastAPI app, Granian)
- `Dockerfile`, `alembic.ini`, `alembic/env.py` шаблон

## Тексты сообщений (русский, в коде)

### Алерт о донате (в alert_topic_id)

```
💰 Новый донат!

{username} задонатил {amount} ₽
{message_part}                  — если был комментарий
{rank_part}                     — место донора в топе
```

Без купюрной поэзии и фразочек-тиров.

### Закреп прогресса (в fundraiser_topic_id)

```
📹 Сбор на камеры для 1 корпуса

⟨▰▰▰▱▱▱▱▱▱▱⟩ 35%
{current_amount} ₽ / {target_amount} ₽

Поддержать → [кнопка Tribute]
```

### Сообщение о завершении (в общий чат)

```
🎉 Сбор завершён!

Собрано {current_amount} ₽ из {target_amount} ₽
Спасибо всем участникам!
```

### Дейли-сводка (DM админам)

```
📊 Сводка за 07.05.2026

За сегодня:
• Собрано: {today_amount} ₽
• Донатов: {today_count}
• Уникальных: {today_unique}

Всего:
• {current_amount} ₽ / {target_amount} ₽
• ⟨▰▰▰▱▱▱▱▱▱▱⟩ 35%
• Осталось: {remaining} ₽

Топ-3:
1. {name} — {amount} ₽
2. ...
```

## Тесты

### Unit (pytest)
- `test_signature.py` — корректные/некорректные подписи, отсутствие заголовка, неверный body
- `test_parser.py` — валидный/невалидный payload, неизвестный event type
- `test_formatting.py` — `format_amount` (целое/дробь, разделители), `calc_progress` (0%, 50%, 100%, >100%)
- `test_donation_service.py` — сохранение, идемпотентность, расчёт ранга

### Integration (testcontainers Postgres)
- `test_tribute_webhook.py` — POST с подписанным телом → запись в БД, ответ 200
- `test_idempotency.py` — повторный вебхук с тем же `donation_request_id` → одна запись
- `test_fundraiser_progress.py` — обновление `current_amount`, авто-закрытие при достижении цели

### E2E
- `test_donation_flow.py` — полный путь с замоканным `Bot`: HMAC-валидный POST → запись → push в очередь → воркер вызывает `bot.send_message` с правильным topic_id и текстом

### Coverage
Цель — ≥80% по `src/`. Не покрываем integration с Telegram API (только мокается).

## Безопасность

- HMAC-проверка обязательна на всех `/tribute` запросах
- Telegram webhook secret token (`X-Telegram-Bot-Api-Secret-Token`) на `/telegram`
- Все секреты — через env (pydantic `SecretStr`)
- Throttling middleware на сообщения и callbacks
- Никакого SQL-инжекшна — только параметризованные запросы через SQLModel
- `comment` от Tribute эскейпится при отправке в Telegram (HTML parse mode → `escape_html`)
- Админ-команды защищены `is_admin` фильтром

## Этапы реализации (для writing-plans)

1. Скаффолдинг проекта: pyproject, Dockerfile, docker-compose, alembic init
2. Конфиг (pydantic-settings) + `.env.example`
3. БД: модели + первая миграция
4. API: HMAC + парсер + роутер `/tribute` + типы
5. Сервисы: donation, notification_queue, fundraiser
6. Scheduler + дейли-сводка
7. aiogram: routers (`/start`, `/stats`, админки), фильтры, мидлвари
8. Тексты сообщений, форматирование, прогресс-бар
9. Тесты (unit → integration → e2e)
10. README + инструкция по деплою

## Верификация

После реализации:
- `docker compose -f docker-compose.local.yml up -d` поднимает сервисы
- `alembic upgrade head` применяет миграции
- `pytest --cov=src --cov-report=term-missing` — все тесты зелёные, ≥80%
- Реальный smoke: `curl -X POST` с валидной HMAC-подписью на `/tribute` → 200 + запись в БД + сообщение в группу (на тестовом чате)
- `/start` в личке боту → приветствие + кнопка
- `/stats` в группе → прогресс
- Дейли-сводка в установленный час приходит админам
