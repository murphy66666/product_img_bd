from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


class MySQLSessionFactory:
    def __init__(self) -> None:
        self._engine = None
        self._sessionmaker = None

    def configure(self) -> None:
        if self._engine is not None:
            return
        settings = get_settings()
        self._engine = create_async_engine(settings.database_url, pool_pre_ping=True)
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
