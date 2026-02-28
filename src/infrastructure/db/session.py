from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import SessionLocal  # используем единый engine и sessionmaker


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session