"""Async SQLAlchemy session for app-metadata Postgres (connections, traces, eval)."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

# Separate metadata DB from target DBs — stores our app state, not customer analytics data.
engine = create_async_engine(
    settings.metadata_database_url,
    echo=False,
    pool_pre_ping=True,
    # /query holds a session for the full LLM pipeline; client timeouts can leave
    # in-flight requests until Groq finishes — size for a few overlapping evals.
    pool_size=10,
    max_overflow=20,
    pool_timeout=60,
)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
