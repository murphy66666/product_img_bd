from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


def mysql_utf8mb4_url(database_url: str) -> str:
    url = make_url(database_url)
    if url.get_backend_name() != "mysql":
        return database_url
    return str(url.update_query_dict({"charset": "utf8mb4"}))


class MySQLSessionFactory:
    def __init__(self) -> None:
        self._engine = None
        self._sessionmaker = None

    def configure(self) -> None:
        if self._engine is not None:
            return
        settings = get_settings()
        self._engine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args={"charset": "utf8mb4"},
        )
        self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)

    async def session(self) -> AsyncIterator[AsyncSession]:
        self.configure()
        assert self._sessionmaker is not None
        async with self._sessionmaker() as session:
            yield session

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None


mysql_sessions = MySQLSessionFactory()


async def check_mysql_connection() -> dict[str, object]:
    """Create an isolated engine for health checks to avoid reusing pooled connections."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, connect_args={"charset": "utf8mb4"})
    try:
        async with engine.connect() as conn:
            selected_value = (await conn.execute(text("SELECT 1"))).scalar_one()
            database_name = (await conn.execute(text("SELECT DATABASE()"))).scalar_one()
            return {"connected": selected_value == 1, "database": database_name}
    finally:
        await engine.dispose()
