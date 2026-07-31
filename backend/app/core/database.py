"""数据库连接与 Session 管理。

使用 SQLAlchemy 2.0 异步引擎（asyncpg / aiosqlite）。
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的声明基类（SQLAlchemy 2.0 风格）。"""

    pass


# 创建异步引擎
# SQLite 需要禁用 check_same_thread；PostgreSQL 无此问题
engine_kwargs: dict = {"echo": settings.DEBUG, "pool_pre_ping": True}
if settings.is_async_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# 异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：获取数据库异步 Session。

    用法：
        @router.get("/")
        async def index(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """初始化数据库表（开发环境使用，生产环境用 Alembic 迁移）。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接池（应用关闭时调用）。"""
    await engine.dispose()
