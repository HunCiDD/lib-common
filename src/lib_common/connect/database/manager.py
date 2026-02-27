from typing import Dict
from threading import Lock

from .schemas import DBConfigsM
from ...designs.singleton import SingletonMeta
from ...settings import Settings
from .base import IDBInfra, IAsyncDBInfra, DBInfraFactory


class DBInfraManager(metaclass=SingletonMeta):
    _databases: Dict[str, IDBInfra | IAsyncDBInfra] = {}

    def __init__(self, settings: Settings, **kwargs):
        self._settings = settings
        self._kwargs = kwargs
        self._lock = Lock()
        self._init_database()

    def _init_database(self):
        for key, db_settings in self._settings.databases.items():
            self._add_database(key=key, cm=db_settings)

    def _add_database(self, key: str, cm: DBConfigsM):
        if not cm.type:
            raise ValueError("DBConfigsM.type cannot be empty")

        database = DBInfraFactory.create(cm.type, key, cm)
        if database:
            self._databases[key] = database

    def get_database(self, key: str) -> IDBInfra | IAsyncDBInfra | None:
        return self._databases.get(key, None)

    def del_database(self, key: str):
        with self._lock:
            if key not in self._databases:
                return

            del self._databases[key]

    def add_database(self, key: str, settings: dict | None = None):
        if settings is None:
            raise ValueError("settings cannot be empty")
        cm = DBConfigsM(**settings)
        self._add_database(key=key, cm=cm)


