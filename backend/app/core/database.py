from typing import AsyncGenerator
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

is_sqlite = "sqlite" in settings.DATABASE_URL
connect_args = {}

if not is_sqlite:
    if "rds.amazonaws.com" in settings.DATABASE_URL:
        connect_args = {
            "ssl": "require",
            "server_settings": {"application_name": "bedrock-gateway"},
            "command_timeout": 30,
            "timeout": 8,
        }
    else:
        connect_args = {
            "command_timeout": 30,
            "timeout": 8,
        }

engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
    "connect_args": connect_args
}
if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
        "pool_timeout": 30
    })

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for yielding an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
