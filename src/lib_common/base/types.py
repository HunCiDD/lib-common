from typing import Annotated, TypeVar
from datetime import datetime
import threading
from collections.abc import MutableMapping
from pathlib import Path

from pydantic import BeforeValidator, Field, StringConstraints

from ..data.generator import DateTimeGenerator
from ..data.regex import RegexPatterns
from ..data.validates import (
    validate_bool,
    validate_host,
    validate_port,
    validate_int,
    validate_lower,
    validate_password,
    validate_path,
    validate_upper,
)


# 动态字典
class DynamicDict(MutableMapping):
    def __init__(self):
        self._storage = {}
        self._lock = threading.RLock()  # 使用可重入锁

    def __setitem__(self, key, value):
        with self._lock:
            self._storage[key] = value

    def __delitem__(self, key):
        with self._lock:
            del self._storage[key]

    def __getitem__(self, key):
        with self._lock:
            return self._storage[key]

    def __len__(self):
        with self._lock:
            return len(self._storage)

    def __iter__(self):
        with self._lock:
            # 返回键的快照的迭代器，避免迭代时持有锁
            keys = list(self._storage.keys())
        return iter(keys)

    def __contains__(self, key):
        with self._lock:
            return key in self._storage

    def __getattr__(self, name):
        if name in ("_storage", "_lock"):
            # 防止通过属性访问 _storage 或 _lock
            raise AttributeError(f"Forbidden attribute '{name}'")
        with self._lock:
            try:
                return self._storage[name]
            except KeyError:
                raise AttributeError(f"Has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in ("_storage", "_lock"):
            # 初始化时绕过自定义 __setattr__
            super().__setattr__(name, value)
        else:
            with self._lock:
                self._storage[name] = value


# 泛型
T = TypeVar("T")

# Bool类型
BoolType = Annotated[str | bool | int, BeforeValidator(validate_bool)]
# 整型类型
IntType = Annotated[str | int, BeforeValidator(validate_int)]
# 大写类型
UpperType = Annotated[str, BeforeValidator(validate_upper)]
# 小写类型
LowerType = Annotated[str, BeforeValidator(validate_lower)]
# 主机类型
HostType = Annotated[str, BeforeValidator(validate_host)]
# 端口类型, 1 <= port <= 65535
PortType = Annotated[str | int, BeforeValidator(validate_port), Field(ge=0, le=65535)]
# 路径类型
PathType = Annotated[str | Path, BeforeValidator(lambda x: validate_path(x))]
ExistPathType = Annotated[str | Path, BeforeValidator(lambda x: validate_path(x, exist=True))]

UsernameType = Annotated[
    str, StringConstraints(min_length=3, max_length=64, pattern=RegexPatterns.Username, strict=True)
]

PasswordType = Annotated[
    str,
    StringConstraints(min_length=8, max_length=128, strict=True),
    BeforeValidator(validate_password),
]

DateTimeType = Annotated[
    datetime,
    Field(
        default_factory=DateTimeGenerator.now,
        description="本地时间",
        examples=[f"{DateTimeGenerator.now().strftime('%Y-%m-%d %H:%M:%S')}"],
    ),
]
