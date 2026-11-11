from pathlib import Path
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_PATH = Path(__file__).resolve().parents[2] / "skyguard.db"
DATABASE_URL = URL.create(
    "sqlite+aiosqlite",
    database=str(DATABASE_PATH),
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def init_db() -> None:
    from app.models.observation import Observation

    if Observation.__tablename__ not in Base.metadata.tables:
        raise RuntimeError("Observation table was not registered with SQLAlchemy metadata.")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session