from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import lstm_engine, router as api_router
from app.core.database import get_db, init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield


app = FastAPI(title="SkyGuard AI - Self-Healing Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def health_check() -> dict[str, object]:
    return {
        "status": "online",
        "onnx_lstm_ready": lstm_engine.ready,
        "database": "connected",
    }


__all__ = ["app", "get_db", "init_db"]
