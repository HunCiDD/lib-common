from libs.common.designs import SingletonMeta

from ..base.manager import ConnectionPoolManager


class DBConnectionPoolManager(ConnectionPoolManager, metaclass=SingletonMeta):
    def _init_pools(self) -> None:
        for key, key_settings in self._run_settings.databases.items():
            self.add_pool(key, key_settings)
