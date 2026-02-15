from ...designs.singleton import SingletonMeta

from ..core.manager import ConnectionPoolManager


class DBConnectionPoolManager(ConnectionPoolManager, metaclass=SingletonMeta):
    def _init_pools(self) -> None:
        for key, key_configs in self._settings.databases.items():
            key_settings = key_configs.model_dump(exclude_unset=True)
            self.add_pool(key, key_settings)
