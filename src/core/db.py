from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from src.core.config import settings


engine = create_async_engine(settings.db_url, echo=True)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session