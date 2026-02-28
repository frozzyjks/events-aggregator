# Events Aggregator

REST API сервис-агрегатор, который интегрируется с Events Provider API и предоставляет расширенные возможности для работы с событиями и мероприятиями.

## Стек

- **Python 3.11+**
- **FastAPI** — веб-фреймворк
- **PostgreSQL** — база данных
- **SQLAlchemy 2.0** — ORM
- **Alembic** — миграции
- **httpx** — HTTP-клиент
- **uv** — менеджер зависимостей
- **ruff** — линтер и форматтер
- **pytest** — тесты

## Запуск

### Через Docker Compose

```bash
docker-compose up --build
```

Swagger UI будет доступен по адресу: `http://localhost:8000/docs`

### Локально

1. Установи зависимости:
```bash
uv sync
```

2. Создай `.env` файл:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/events
EVENTS_API_URL=https://events-provider.dev-2.python-labs.ru
EVENTS_API_KEY=your_api_key_here
```

3. Примени миграции:
```bash
uv run alembic upgrade head
```

4. Запусти сервер:
```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## API

Сервис автоматически синхронизирует события с Events Provider API раз в день. Первая синхронизация получает все события, последующие — только изменённые.

### События

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/api/events` | Список событий с фильтрацией и пагинацией |
| GET | `/api/events/{event_id}` | Детали события |
| GET | `/api/events/{event_id}/seats` | Свободные места (кэш 30 сек) |

Query параметры для `GET /api/events`:

| Параметр | Тип | Описание |
|---|---|---|
| `date_from` | YYYY-MM-DD | События после указанной даты |
| `date_to` | YYYY-MM-DD | События до указанной даты |
| `name` | string | Фильтр по названию |
| `status` | string | Фильтр по статусу |
| `page` | int | Номер страницы (по умолчанию 1) |
| `page_size` | int | Размер страницы (по умолчанию 20, макс 100) |

### Тикеты

| Метод | Endpoint | Описание |
|---|---|---|
| POST | `/api/tickets` | Регистрация на событие |
| DELETE | `/api/tickets/{ticket_id}` | Отмена регистрации |

## Тесты

```bash
uv run pytest tests/ -v
```

## Линтер

```bash
uv run ruff check .
uv run ruff format --check .
```

## CI

GitHub Actions автоматически запускает линтер и тесты при пуше в `main`.