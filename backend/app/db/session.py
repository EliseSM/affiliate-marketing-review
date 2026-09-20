from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

# statement_cache_size=0 disables asyncpg's prepared-statement cache, which is
# required against Supabase's pooled/transaction-mode pgbouncer connection --
# pgbouncer in transaction mode doesn't preserve prepared statements across the
# pooled connections it hands out, so asyncpg's caching causes
# "DuplicatePreparedStatementError" under concurrent/repeated use.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    connect_args={"statement_cache_size": 0},
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
