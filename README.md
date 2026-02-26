# Events Aggregator

Backend service for aggregating events.

## Tech Stack

- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy (async)
- Alembic
- Docker

## Run locally

### Docker

```bash
docker compose up --build
```
Service available at:
```bash
http://localhost:8000/docs
```
Run migrations manually
```bash
docker compose exec app uv run alembic upgrade head
```