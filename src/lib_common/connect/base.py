from typing import Any

from ...mixins import TypeMixin
from ..designs.factory import RegisterFactory
from .schemas import InfraConfigsM


# 同步设施
class IInfra(ABC, Generic[T]):
    @abstractmethod
    def get_connection(self) -> T: ...

    @abstractmethod
    def release_connection(self, conn: T): ...

    def connection(self): ...


# 异步设施
class IAsyncInfra(ABC, Generic[T]):
    @abstractmethod
    async def get_connection(self) -> T: ...

    @abstractmethod
    async def release_connection(self, conn: T): ...

    async def connection(self): ...


# 基础设施工厂
class InfraFactory(RegisterFactory[IInfra | IAsyncInfra]):
    _map = {}



