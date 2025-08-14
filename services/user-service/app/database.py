from __future__ import annotations

from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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
connect_args: dict[str, dict[str, str]] = {}

if "options=" in database_url:
    split_url = urlsplit(database_url)
    query_params = dict(parse_qsl(split_url.query))
    options = query_params.pop("options", None)
    if options and options.startswith("-csearch_path="):
        search_path = options.split("=", 1)[1]
        connect_args["server_settings"] = {"search_path": search_path}
    database_url = urlunsplit(
        (
            split_url.scheme,
            split_url.netloc,
            split_url.path,
            urlencode(query_params),
            split_url.fragment,
        )
    )

if database_url.startswith("sqlite://") and not database_url.startswith(
    "sqlite+aiosqlite://"
):
    database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
if database_url.startswith("sqlite+aiosqlite://"):
    metadata.schema = None

async_engine = create_async_engine(database_url, connect_args=connect_args)
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
