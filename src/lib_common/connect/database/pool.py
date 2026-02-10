from __future__ import annotations

from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


from lib_common.data.utils.validates import validate_path
from .schemas import DatabaseConfigs
from ..core.interface import IConnectionPool, IAsyncConnectionPool
from ..core.pool import BaseConnectionPool
from ..core.factory import ConnectionPoolFactory

from ...configs import loggers


run_logger = loggers.get_logger("run")


class BaseSQLAlchemyDBConnectionPool(BaseConnectionPool):
    def __init__(self, configs: DatabaseConfigs, **kwargs):
        self.configs = configs
        super().__init__(self.configs.infra, **kwargs)
        self.url = ""
        self._init_url()
        self.engine_kwargs = {}
        self._init_engine_kwargs()

    def _init_url(self):
        dialect, driver, file = self.configs.dialect, self.configs.driver, self.configs.file
        database = self.configs.database
        username, password = self.infra.username, self.infra.password

        if dialect == "sqlite":
            if ":memory:" == file.name:
                file = ":memory:"
            else:
                if file:
                    validate_path(file, exist=True)

            if driver == "":
                self.url = f"{dialect}:///{file}"
            elif driver == "aiosqlite":
                self.url = f"{dialect}+{driver}:///{file}"

        elif dialect in ["mysql", "postgresql"]:
            self.url = f"{dialect}+{driver}://{username}:{password}@{self.infra.netloc}/{database}"

    def _init_engine_kwargs(self):
        if "sqlite" in self.url and ":memory:" in self.url:
            engine_kwargs = {
                "connect_args": {"check_same_thread": False},
            }
        else:
            engine_kwargs = {
                "pool_pre_ping": True,  # 使用前检查连接是否有效
                "pool_recycle": 300,  # 每5分钟回收连接(秒) - 防止服务器超时断开
                "pool_size": 10,  # 连接池大小
                "max_overflow": 20,  # 允许超过pool_size的连接数
                "pool_timeout": 30,  # 获取连接超时时间(秒)
                "connect_args": {
                    "command_timeout": 60,  # 单个命令超时时间(秒)
                    "server_settings": {"application_name": "ai-life-py"},
                },
            }
        self.engine_kwargs = engine_kwargs


class SQLAlchemyDBConnectionContext:
    def __init__(self, pool: SQLAlchemyDBConnectionPool):
        self.pool = pool
        self.session = None

    def __enter__(self) -> Session:
        self.session = self.pool.get_connection()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时处理连接"""
        if self.session is None:
            return False

        try:
            if exc_type is None:
                # 没有异常时提交事务
                self.session.commit()
            else:
                # 有异常时回滚事务
                self.session.rollback()
                run_logger.exception(f"Exception in session context: {exc_val}")
        except Exception as e:
            run_logger.exception(f"Error during session cleanup: {e}")
            # 如果清理过程中出错，仍然需要关闭会话
        finally:
            # 确保会话被关闭
            self.pool.release_connection(self.session)
            self.session = None

        # 返回 False 表示不抑制异常
        return False


class AsyncSQLAlchemyDBConnectionContext:
    def __init__(self, pool: AsyncSQLAlchemyDBConnectionPool):
        self.pool = pool
        self.session = None

    async def __aenter__(self) -> AsyncSession:
        self.session = await self.pool.get_connection()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.session:
            return False

        try:
            if exc_type is None:
                # 没有异常时提交事务
                await self.session.commit()
            else:
                await self.session.rollback()
                run_logger.exception(f"Exception in session context: {exc_val}")
        except Exception as e:
            run_logger.exception(f"Error during session cleanup: {e}")
            # 如果清理过程中出错，仍然需要关闭会话
        finally:
            # 确保会话被关闭
            await self.pool.release_connection(self.session)
            self.session = None

        # 返回 False 表示不抑制异常
        return False


@ConnectionPoolFactory.register("SQLAlchemyDBConnectionPool")
class SQLAlchemyDBConnectionPool(BaseSQLAlchemyDBConnectionPool, IConnectionPool[Session]):
    def __init__(self, configs: DatabaseConfigs, **kwargs):
        super().__init__(configs, **kwargs)
        self.engine: Engine = create_engine(self.url, echo=self.configs.echo, **self.engine_kwargs)
        self.session_factory = sessionmaker(self.engine, autoflush=False)

    def get_connection(self) -> Session:
        session = self.session_factory()
        return session

    def release_connection(self, conn: Session):
        conn.close()

    def connection(self) -> SQLAlchemyDBConnectionContext:
        """上下文管理器获取连接"""
        return SQLAlchemyDBConnectionContext(self)


@ConnectionPoolFactory.register("AsyncSQLAlchemyDBConnectionPool")
class AsyncSQLAlchemyDBConnectionPool(BaseSQLAlchemyDBConnectionPool, IAsyncConnectionPool[AsyncSession]):
    def __init__(self, configs: DatabaseConfigs, **kwargs):
        super().__init__(configs, **kwargs)
        self.engine_kwargs = {}
        self.engine: AsyncEngine = create_async_engine(self.url, echo=self.configs.echo, **self.engine_kwargs)
        self.session_factory = async_sessionmaker(
            self.engine, autoflush=False, expire_on_commit=False, class_=AsyncSession
        )

    async def get_connection(self) -> AsyncSession:
        return self.session_factory()

    async def release_connection(self, conn: AsyncSession):
        await conn.close()

    def connection(self) -> AsyncSQLAlchemyDBConnectionContext:
        """上下文管理器获取连接"""
        return AsyncSQLAlchemyDBConnectionContext(self)
