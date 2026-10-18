from __future__ import annotations
import json
import logging
from collections.abc import AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import DB_PATH, DEFAULT_SETTINGS, ensure_data_directories
from .models import Base, SchemaVersion, Setting

logger = logging.getLogger("hangar.db")

CURRENT_SCHEMA_VERSION = 1

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        ensure_data_directories()
        # aiosqlite connection url
        db_url = f"sqlite+aiosqlite:///{DB_PATH}"
        _engine = create_async_engine(db_url, echo=False)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI route handlers."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database tables, schema version, and seed default settings."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = get_session_factory()
    async with factory() as session:
        # Check / set schema version
        result = await session.execute(select(SchemaVersion).order_by(SchemaVersion.version.desc()))
        current = result.scalars().first()
        if not current:
            session.add(SchemaVersion(version=CURRENT_SCHEMA_VERSION))
            await session.commit()

        # Seed default settings if missing
        for key, val in DEFAULT_SETTINGS.items():
            setting_res = await session.execute(select(Setting).where(Setting.key == key))
            if not setting_res.scalar_one_or_none():
                session.add(Setting(key=key, value=json.dumps(val)))
        await session.commit()
    logger.info("Database initialized at %s", DB_PATH)


async def close_db() -> None:
    """Close async database engine."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None

