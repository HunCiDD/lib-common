from typing import Dict
from threading import Lock

from ...settings import Settings
from .interface import IConnectionPool, IAsyncConnectionPool
from .schemas import InfraM
from .factory import ConnectionPoolFactory


class ConnectionPoolManager:
    _pools: Dict[str, IConnectionPool | IAsyncConnectionPool] = {}

    def __init__(self, settings: Settings, **kwargs):
        self._settings = settings
        self._kwargs = kwargs
        self._lock = Lock()
        self._init_pools()

    def _init_pools(self) -> None: ...

    def add_pool(self, key: str, settings: dict | None = None) -> None:
        if settings is None:
            raise ValueError

        pool_type = settings.get("poolType", "")
        if not pool_type:
            raise ValueError

        infra = InfraM(**settings.get("infra", {}))
        _settings = settings.get("settings", {})

        pool = ConnectionPoolFactory.create(pool_type, infra, _settings)
        if pool:
            self.del_pool(key)
            self._pools[key] = pool

    def get_pool(self, key: str) -> IConnectionPool | IAsyncConnectionPool | None:
        return self._pools.get(key, None)

    def del_pool(self, key: str) -> None:
        with self._lock:
            if key not in self._pools:
                return
            del self._pools[key]
