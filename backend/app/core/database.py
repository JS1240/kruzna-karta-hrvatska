from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

sync_engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

async_db_url = (
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    if settings.database_url.startswith("postgresql://")
    else settings.database_url
)
async_engine = create_async_engine(async_db_url)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

Base = declarative_base()


def get_db():
    """Database dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncSession:
    """Async database dependency for FastAPI."""
    async with AsyncSessionLocal() as session:
        yield session
