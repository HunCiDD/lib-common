from typing import Dict

from ..designs.singleton import SingletonMeta
from .base import Cryptor
from ..settings import Settings


class CryptorManager(metaclass=SingletonMeta):
    _cryptors: Dict[str, Cryptor] = {}

    def __init__(self, settings: Settings, **kwargs):
        self._settings = settings
        if not self._settings.cryptors:
            raise ValueError("未配置加密")

        if not self._settings.cryptors.root:
            raise ValueError("未配置根加密")

        self._kwargs = kwargs
        self._init_cryptors()

    def _init_cryptors(self):
        for key, work_configs in self._settings.cryptors.work.items():
            work_secret = work_configs.secret.get_secret_value()
            if not work_secret:
                continue
            self._add_cryptor(key, work_secret.encode("utf-8"), xform=work_configs.xform)

    def _add_cryptor(self, key: str, work_key: bytes | None = None, xform: str = "aes/gcm/pkcs7") -> Cryptor | None:
        if not work_key:
            return None
        ct = Cryptor(config=self._settings.cryptors.root, work_key=work_key, xform=xform)
        self._cryptors[key] = ct
        return ct

    def add_cryptor(self, key: str, work_key: bytes | None = None, xform: str = "aes/gcm/pkcs7") -> Cryptor | None:
        self.del_cryptor(key)
        return self._add_cryptor(key, work_key, xform=xform)

    def del_cryptor(self, key: str):
        if key in self._cryptors:
            del self._cryptors[key]

    def get_cryptor(self, key: str) -> Cryptor | None:
        if key in self._cryptors:
            return self._cryptors[key]

        # 不在缓存中，检查配置中是否存在，创建并返回
        if key in self._cryptors:
            key_settings = self._settings.get(key, b"")
            return self._add_cryptor(key, key_settings)
        return None
