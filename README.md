# Lightbulb Factory — микросервисы

Бэкенд интернет-магазина «Lightbulb Factory» из двух сервисов. Монорепозиторий, локальный запуск через `docker compose`.

## Обзор

Два независимых Python-микросервиса:

- **`products_microservice/`** — каталог товаров, справочники (категории, типы ламп, формы колб, цоколи, поставщики, промо) и отзывы. Слушает порт `8002`.
- **`orders_microservice/`** — создание, чтение и смена статуса заказов. Слушает порт `8003`. Ходит в `products_microservice` по HTTP, чтобы валидировать позиции и снапшотить цены на момент оформления заказа.

**Стек:**

- Python 3.11+
- FastAPI (асинхронный веб-фреймворк)
- SQLAlchemy 2.x (async ORM) + `asyncpg`
- PostgreSQL — один инстанс, две логические БД: `products_db`, `orders_db`
- Alembic — миграции схемы, отдельно для каждого сервиса
- Pydantic v2 / Pydantic Settings — валидация и конфиг
- pytest + pytest-asyncio + httpx — тесты
- Docker + корневой `docker-compose.yml` — оркестрация

Аутентификация и авторизация в этой итерации вне скоупа. Поля аудита `created_by` / `edited_by` в схеме есть как nullable UUID — на будущее, но сейчас всегда пишутся как `NULL`.

## Требования

- Docker (>= 24) и Docker Compose v2
- Python 3.11+ (нужен только если запускаешь тесты или миграции напрямую с хоста)
- GNU Make

## Структура репозитория

```
.
├── products_microservice/   # Товары + отзывы + справочники (порт 8002)
├── orders_microservice/     # Заказы + позиции заказа (порт 8003)
├── docs/                    # Архитектурные диаграммы, ER-диаграммы, Postman, юзерфлоу
├── tests_e2e/               # E2E-тесты против поднятого стека
├── scripts/                 # Сервисные шелл-скрипты (наполнение тестовыми данными и т.п.)
├── docker-compose.yml       # Полный локальный стек
├── Makefile                 # Корневые цели dev/test/migrate/lint
├── .env.example             # Шаблон обязательных переменных окружения
└── README.md
```

У каждого микросервиса свои `app/`, `tests/`, `alembic/`, `pyproject.toml` и `Dockerfile`.

## Быстрый старт

```bash
cp .env.example .env
$EDITOR .env

make build
make up

curl http://localhost:8002/health
curl http://localhost:8003/health
```

Поднимаются:

- `postgres` — один контейнер, в нём обе БД (`products_db`, `orders_db`)
- `products_service` — Products-микросервис на `http://localhost:8002`
- `orders_service` — Orders-микросервис на `http://localhost:8003`

Остановить стек: `make down`. Логи: `make logs`.

## Переменные окружения

Все переменные читаются из `.env` в корне репозитория (см. `.env.example`).

| Переменная                   | Обязательная | Default / Заметки                                                                |
|------------------------------|--------------|-----------------------------------------------------------------------------------|
| `POSTGRES_USER`              | да           | Суперпользователь Postgres, под ним создаются обе логические БД.                  |
| `POSTGRES_PASSWORD`          | **да**       | Дефолта нет; если не задан — compose сразу падает.                                |
| `POSTGRES_DB`                | да           | Стартовая БД (оставлено `postgres`); init-скрипт создаёт `products_db` и `orders_db`. |
| `PRODUCTS_DATABASE_URL`      | **да**       | Async DSN, например `postgresql+asyncpg://<user>:<pass>@postgres:5432/products_db`. |
| `ORDERS_DATABASE_URL`        | **да**       | Async DSN, например `postgresql+asyncpg://<user>:<pass>@postgres:5432/orders_db`.   |
| `PRODUCTS_REQUEST_TIMEOUT_S` | нет          | По умолчанию `2.0`. Таймаут на запрос Orders → Products.                          |
| `ENVIRONMENT`                | нет          | По умолчанию `development`. Свободная строка (`development` / `test` / `production`). |
| `LOG_LEVEL`                  | нет          | По умолчанию `INFO`.                                                              |

`PRODUCTS_BASE_URL` задаётся внутри `docker-compose.yml` как `http://products_service:8002` — добавлять в `.env` не нужно.

## Порты

| Сервис    | Порт хоста | Порт контейнера | Заметки                              |
|-----------|------------|-----------------|--------------------------------------|
| Products  | 8002       | 8002            | FastAPI                              |
| Orders    | 8003       | 8003            | FastAPI                              |
| Postgres  | 5432       | 5432            | Слушает только `127.0.0.1` (loopback). |

## Запуск тестов

```bash
source .venv/bin/activate
make test                  # оба сервиса
make test-products
make test-orders
```

E2E-тесты в `tests_e2e/` требуют поднятого стека (`make up`), иначе скипаются. Подробнее — `tests_e2e/README.md`.

## Наполнение тестовыми данными

Готовый bash-скрипт `scripts/seed_test_data.sh` создаёт справочники, продукты, отзывы и заказы за один прогон — удобно для ручной проверки или демо.

```bash
make up                                 # стек должен быть поднят
./scripts/seed_test_data.sh
```

Что создаётся:

- **Справочники в Products:** 3 категории, 3 типа ламп, 3 формы колб, 4 цоколя, 3 поставщика, 2 промо.
- **Продукты:** 6 штук с разными комбинациями FK, ценами и наличием.
- **Отзывы:** 6 отзывов с рейтингами 2–5 на разные продукты.
- **Заказы в Orders:** 3 заказа (Alice / Bob / Carol) с 1, 3 и 2 позициями. Orders при создании ходит в Products валидировать каждый `product_id` и снапшотить `current_price`.

Переопределить адреса сервисов:

```bash
PRODUCTS_URL=http://localhost:9002 ORDERS_URL=http://localhost:9003 ./scripts/seed_test_data.sh
```

Особенности:

- Скрипт идемпотентен по уникальным полям: к именам/email добавляется суффикс `${unix_ts}-${RANDOM}`, можно прогонять много раз без коллизий.
- При первой же 4xx/5xx прерывается с понятной ошибкой (URL, статус, тело ответа).
- Зависимости: `curl` и `python3` (распарсить ID из ответа). `jq` не нужен.

Посмотреть, что получилось:

```bash
curl -s http://localhost:8002/api/v1/products?size=20 | python3 -m json.tool
curl -s http://localhost:8003/api/v1/orders            | python3 -m json.tool
```

## Миграции

У каждого сервиса своя конфигурация Alembic, миграции применяются автоматически при старте контейнера. Прогнать миграции против поднятой БД с хоста:

```bash
make migrate-products
make migrate-orders
```

## Межсервисное взаимодействие

При создании заказа Orders дёргает Products по двум причинам:

1. **Существование и активность товара** — подтверждается через `GET /api/v1/products/{id}`.
2. **Снапшот цены** — `current_price` каждой позиции `OrderItem` берётся из ответа Products и сохраняется. Поэтому последующие изменения цены не переписывают исторические заказы задним числом.

HTTP-клиент с настраиваемым таймаутом (`PRODUCTS_REQUEST_TIMEOUT_S`) и небольшим бюджетом ретраев. При устойчивом сбое апстрима создание заказа возвращает **`503 Service Unavailable`**. Сервисы напрямую не лазят друг другу в БД.

## Краткое API

### Products (`http://localhost:8002`)

| Метод  | Путь                                   | Назначение                              |
|--------|----------------------------------------|-----------------------------------------|
| GET    | `/health`                              | Liveness-проба                          |
| GET    | `/api/v1/categories` (и 5 «братьев»)   | Список справочника                      |
| POST   | `/api/v1/categories` (и 5 «братьев»)   | Создать запись справочника              |
| PUT    | `/api/v1/categories/{id}`              | Обновить запись справочника             |
| DELETE | `/api/v1/categories/{id}`              | Удалить (с защитой от удаления, если используется в продукте) |
| GET    | `/api/v1/products`                     | Постраничный список с фильтрами         |
| GET    | `/api/v1/products/{id}`                | Один продукт                            |
| POST   | `/api/v1/products`                     | Создать продукт                         |
| PUT    | `/api/v1/products/{id}`                | Обновить продукт                        |
| DELETE | `/api/v1/products/{id}`                | Удалить продукт                         |
| GET    | `/api/v1/reviews?product_id={id}`      | Отзывы по продукту                      |
| POST   | `/api/v1/reviews`                      | Создать отзыв (`product_id` в теле)     |
| DELETE | `/api/v1/reviews/{review_id}`          | Удалить отзыв                           |

Пять «братских» справочников: `bulb-types`, `bulb-shapes`, `sockets`, `suppliers`, `promos`.

### Orders (`http://localhost:8003`)

| Метод  | Путь                          | Назначение                                                       |
|--------|-------------------------------|------------------------------------------------------------------|
| GET    | `/health`                     | Liveness-проба                                                   |
| POST   | `/api/v1/orders`              | Создать заказ (валидирует продукты + снапшотит цену)             |
| GET    | `/api/v1/orders`              | Список заказов, опционально фильтр `status`                      |
| GET    | `/api/v1/orders/{id}`         | Один заказ с позициями                                           |
| PATCH  | `/api/v1/orders/{id}`         | Сменить статус (разрешённые переходы проверяются на сервере)     |

Полный референс запросов/ответов — в `docs/postman_collection.json`.

## Траблшутинг

- **Orders не может достучаться до Products.** Проверь, что `PRODUCTS_BASE_URL` внутри контейнера orders резолвится в `http://products_service:8002` (это compose-дефолт). Если запускаешь orders вне Docker — укажи `http://localhost:8002`.

- **Конфликт порта Postgres при `make up`.** Postgres биндится на `127.0.0.1:5432`. Если порт уже занят локальным Postgres, поправь хостовую часть `ports:` в `docker-compose.yml`, например `127.0.0.1:5433:5432`.

- **Alembic падает при первом запуске / миграции при старте контейнера.** Убедись, что `PRODUCTS_DATABASE_URL` и `ORDERS_DATABASE_URL` заданы в `.env` и используют драйвер `postgresql+asyncpg://`. Если от прошлого запуска осталась битая схема — снеси тома: `docker compose down -v` и пересобери.

- **Тесты не видят модули `app`.** Активируй корневой `.venv` (`source .venv/bin/activate`) перед `pytest`; оба сервиса установлены туда в editable-режиме.

## Документация

Архитектурные диаграммы, ER-диаграммы, матрицы страниц/прав, юзерфлоу и Postman-коллекция лежат в `docs/`.

## Лицензия

См. `LICENSE`.
