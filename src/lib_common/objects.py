# 自定义数据结构
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
