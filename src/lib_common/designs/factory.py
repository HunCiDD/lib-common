# 工厂模式
from typing import Generic

from ..types import T


# 注册工厂
class RegisterFactory(Generic[T]):
    @classmethod
    def register(cls, name: str):
        def wrapper(request_cls: type) -> type:
            # 确保每个子类有自己的 _map
            if not hasattr(cls, "_map"):
                cls._map = {}
            cls._map[name] = request_cls
            return request_cls

        return wrapper

    @classmethod
    def create(cls, name: str, *args, **kwargs) -> T | None:
        # 确保每个子类有自己的 _map
        if not hasattr(cls, "_map"):
            cls._map = {}

        if name not in cls._map:
            return None
        return cls._map[name](*args, **kwargs)
