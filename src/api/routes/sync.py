from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.clients.events_provider import get_events_client
from src.infrastructure.db.session import get_session
from src.services.sync_service import SyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/trigger")
async def trigger_sync(
    session: AsyncSession = Depends(get_session),
):
    client = get_events_client()
    service = SyncService(client=client, session=session)
    try:
        await service.run()
    except Exception as exc:
        logger.exception("Manual sync failed")
        raise HTTPException(status_code=500, detail=f"Sync failed: {exc}")
    return {"status": "ok"}