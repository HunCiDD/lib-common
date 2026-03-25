# 自定义数据结构
from typing import Dict, Any
import threading
from collections.abc import MutableMapping


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


class Context:
    """支持点分隔路径访问的嵌套字典容器上下文"""

    def __init__(self, data: Dict[str, Any] = None):
        self._data = data if data else {}

    def get(self, path: str, default: Any = None):
        """
        通过点分隔路径获取值。
        :param path: 点分隔路径，例如 "a.b.c"
        :param default: 路径不存在时返回的默认值
        :return: 路径对应的值，或默认值
        """
        keys = path.split(".")
        d = self._data
        for key in keys:
            if isinstance(d, dict) and key in d:
                d = d[key]
            else:
                return default
        return d

    def set(self, path: str, value: Any):
        """
        通过点分隔路径设置值。路径中缺失的键会自动创建为字典。
        :param path: 点分隔路径
        :param value: 要设置的值
        :raises TypeError: 若路径中某中间值不是字典且不为空，无法继续创建子键
        """
        keys = path.split(".")
        d = self._data
        # 遍历到倒数第二个键，确保父级存在
        for key in keys[:-1]:
            if key not in d:
                d[key] = {}
            elif not isinstance(d[key], dict):
                raise TypeError(f"路径中的 '{key}' 不是字典，无法设置子键")
            d = d[key]
        # 设置最后一个键的值
        d[keys[-1]] = value

    @property
    def data(self):
        return self._data
