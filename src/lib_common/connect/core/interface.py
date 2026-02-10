from __future__ import annotations
from abc import abstractmethod, ABC
from typing import Generic

from ...types import T
from .base import BaseRequest, BaseResponse


# ------------------- 请求 ---------------------
class IRequest(ABC):
    @abstractmethod
    def validate(self) -> bool: ...

    @abstractmethod
    def build(self): ...


# ------------------- 响应 ---------------------
class IResponse(ABC):
    @abstractmethod
    def validate(self) -> bool: ...

    @abstractmethod
    def process(self): ...


# ------------------- 连接池 ---------------------
class IConnectionPool(ABC, Generic[T]):
    """同步连接池"""

    @abstractmethod
    def get_connection(self) -> T:
        """获取一个连接"""
        ...

    @abstractmethod
    def release_connection(self, conn: T):
        """释放一个连接"""
        ...

    def connection(self):
        """上下文管理器获取连接"""
        ...


class IAsyncConnectionPool(ABC, Generic[T]):
    """异步连接池"""

    @abstractmethod
    async def get_connection(self) -> T: ...

    @abstractmethod
    async def release_connection(self, conn: T): ...

    async def connection(self): ...


# ------------------- 调用器 ---------------------
class ICaller(ABC):
    @abstractmethod
    def send(self, request: IRequest) -> BaseResponse:
        """发送连接"""
        ...


class IAsyncCaller(ABC):
    @abstractmethod
    async def send(self, request: IRequest) -> BaseResponse:
        """发送连接"""
        ...
