from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import SyncMetadata


class SyncMetadataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self) -> SyncMetadata:
        result = await self._session.execute(select(SyncMetadata).limit(1))
        meta = result.scalars().first()
        if meta is None:
            meta = SyncMetadata(id=1)
            self._session.add(meta)
            await self._session.flush()
        return meta