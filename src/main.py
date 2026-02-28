from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.events import router as events_router
from src.api.routes.sync import router as sync_router
from src.infrastructure.clients.events_provider import get_events_client
from src.infrastructure.db.session import get_session_ctx
from src.services.sync_service import SyncService

logger = logging.getLogger(__name__)

SYNC_INTERVAL_SECONDS = 24 * 60 * 60


async def _background_sync_worker() -> None:
    while True:
        try:
            async with get_session_ctx() as session:
                client = get_events_client()
                service = SyncService(client=client, session=session)
                await service.run()
        except Exception:
            logger.exception("Background sync error")
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_background_sync_worker())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

app.include_router(events_router)
app.include_router(sync_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}