from collections.abc import AsyncGenerator
from typing import Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from app.config import settings

# Lazily create engine and session factory so they bind to the running
# event loop when first used. This avoids attaching asyncpg/engine
# internals to an event loop created by a prior script run
# (which causes "Future attached to a different loop" errors).
_engine: Optional[AsyncEngine] = None
_AsyncSessionFactory: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.is_development,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory() -> async_sessionmaker:
    global _AsyncSessionFactory
    if _AsyncSessionFactory is None:
        _AsyncSessionFactory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _AsyncSessionFactory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
# Backwards-compatible lazy proxies for older code that imports
# `AsyncSessionFactory` or `engine` directly from this module.
class _LazySessionFactory:
    def __call__(self, *args, **kwargs):
        return get_session_factory()(*args, **kwargs)


class _LazyEngine:
    def __getattr__(self, item):
        return getattr(get_engine(), item)


# Expose compatibility names expected across the codebase and scripts.
AsyncSessionFactory = _LazySessionFactory()
engine = _LazyEngine()
