from __future__ import annotations
from typing import List, Generic
from abc import ABC, abstractmethod

from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ...types import T
from ...designs.factory import RegisterFactory
from ...data.utils.validates import validate_path
from .schemas import DBConfigsM


class Base(DeclarativeBase): ...


class BaseModel(Base):
    __abstract__ = True

    def as_dict(self, relations: List[str] = None, **kwargs) -> dict:
        # 将基础列转换成字典
        _dict = {name: getattr(self, name) for name, _ in self.__table__.columns.items()}
        if not relations:
            return _dict

        # 将关系属性转换成字典
        for key in relations:
            _dict[key] = None
            try:
                relations_value = getattr(self, key)
                if not relations_value:
                    continue

                if isinstance(relations_value, BaseModel):
                    _dict[key] = relations_value.as_dict()
                elif isinstance(relations_value, list):
                    _dict[key] = [relation.as_dict() for relation in relations_value]

            except Exception:
                pass

        return _dict


# 同步设施
class IDBInfra(ABC, Generic[T]):
    @abstractmethod
    def get_connection(self) -> T: ...

    @abstractmethod
    def release_connection(self, conn: T): ...

    def connection(self): ...


# 异步设施
class IAsyncDBInfra(ABC, Generic[T]):
    @abstractmethod
    async def get_connection(self) -> T: ...

    @abstractmethod
    async def release_connection(self, conn: T): ...

    async def connection(self): ...


# 基础设施工厂
class DBInfraFactory(RegisterFactory[IDBInfra | IAsyncDBInfra]):
    _map = {}


class DBInfra:
    def __init__(self, name: str, cm: DBConfigsM = None, **kwargs) -> None:
        self.name = name
        self.kwargs = kwargs
        self.cm = cm

    @property
    def url(self) -> str:
        dialect, driver = self.cm.dialect, self.cm.driver
        username, password = self.cm.infra.username, self.cm.infra.password
        netloc = self.cm.infra.netloc
        database = self.cm.database
        file = self.cm.file

        if dialect == "sqlite":
            if ":memory:" == file.name:
                file = ":memory:"
            else:
                validate_path(file, exist=True)

            if driver == "":
                return f"{dialect}:///{file}"
            else:
                return f"{dialect}+{driver}:///{file}"
        else:
            return f"{dialect}+{driver}://{username}:{password}@{netloc}/{database}"

    @property
    def engine_configs(self) -> dict:
        if self.cm.dialect == "sqlite" and self.cm.file.name == ":memory:":
            return {
                "connect_args": {"check_same_thread": False},
            }
        else:
            return {
                "pool_pre_ping": True,      # 使用前检查连接是否有效
                "pool_recycle": 300,        # 每5分钟回收连接(秒) - 防止服务器超时断开
                "pool_size": 10,            # 连接池大小
                "max_overflow": 20,         # 允许超过pool_size的连接数
                "pool_timeout": 30,         # 获取连接超时时间(秒)
                "connect_args": {
                    "command_timeout": 60,  # 单个命令超时时间(秒)
                },
            }


class SQLAlchemyDBConnectionContext:
    def __init__(self, db: SQLAlchemyDB):
        self.db = db
        self.session = None

    def __enter__(self) -> Session:
        self.session = self.db.get_connection()
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
                print(f"Exception in session context: {exc_val}")
        except Exception as e:
            print(f"Error during session cleanup: {e}")
            # 如果清理过程中出错，仍然需要关闭会话
        finally:
            # 确保会话被关闭
            self.db.release_connection(self.session)
            self.session = None

        # 返回 False 表示不抑制异常
        return False


@DBInfraFactory.register("SQLAlchemyDB")
class SQLAlchemyDB(DBInfra, IDBInfra):

    def __init__(self, name: str, cm: DBConfigsM = None, **kwargs) -> None:
        super().__init__(name, cm, **kwargs)
        self.engine: Engine = create_engine(self.url, echo=self.cm.echo, **self.engine_configs)
        self.session_factory = sessionmaker(self.engine, autoflush=False)


    def get_connection(self) -> Session:
        session = self.session_factory()
        return session

    def release_connection(self, conn: Session):
        conn.close()

    def connection(self) -> SQLAlchemyDBConnectionContext:
        """上下文管理器获取连接"""
        return SQLAlchemyDBConnectionContext(self)


class AsyncSQLAlchemyDBConnectionContext:
    def __init__(self, db: AsyncSQLAlchemyDB):
        self.db = db
        self.session = None

    async def __aenter__(self) -> AsyncSession:
        self.session = await self.db.get_connection()
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
                print(f"Exception in session context: {exc_val}")
        except Exception as e:
            print(f"Error during session cleanup: {e}")
            # 如果清理过程中出错，仍然需要关闭会话
        finally:
            # 确保会话被关闭
            await self.db.release_connection(self.session)
            self.session = None

        # 返回 False 表示不抑制异常
        return False


@DBInfraFactory.register("AsyncSQLAlchemyDB")
class AsyncSQLAlchemyDB(DBInfra, IAsyncDBInfra):
    def __init__(self, name: str, cm: DBConfigsM = None, **kwargs) -> None:
        super().__init__(name, cm, **kwargs)
        self.engine: AsyncEngine = create_async_engine(self.url, echo=self.cm.echo)
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

