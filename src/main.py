from fastapi import FastAPI
from src.api.routes.events import router as events_router
from src.core.db import engine, Base

app = FastAPI()

app.include_router(events_router)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/api/health")
async def health():
    return {"status": "ok"}