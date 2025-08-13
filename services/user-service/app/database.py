from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .settings import get_settings

metadata = MetaData(schema="users")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    metadata = metadata


settings = get_settings()

database_url = str(settings.database_url)
if database_url.startswith("sqlite://") and not database_url.startswith(
    "sqlite+aiosqlite://"
):
    database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
if database_url.startswith("sqlite+aiosqlite://"):
    metadata.schema = None

async_engine = create_async_engine(database_url)
async_session_factory = async_sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)

# Expose a synchronous engine and session factory for compatibility with tests
sync_database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
engine = create_engine(sync_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
