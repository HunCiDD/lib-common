from typing import Dict

from ..designs.singleton import SingletonMeta
from ..common.settings import AppRunSettings
from .cryptor import Cryptor


class CryptorManager(metaclass=SingletonMeta):
    _cryptors: Dict[str, Cryptor] = {}

    def __init__(self, run_settings: AppRunSettings, **kwargs):
        self._run_settings = run_settings
        self._settings = self._run_settings.cryptors
        self._kwargs = kwargs
        self._init_cryptors()

    def _init_cryptors(self):
        for key, key_settings in self._settings.items():
            work_key = key_settings.get("work_key", "")
            xform = key_settings.get("xform", "aes/gcm/pkcs7")
            if not work_key:
                continue
            self._add_cryptor(key, work_key, xform=xform)

    def _add_cryptor(self, key: str, work_key: bytes | None = None, xform: str = "aes/gcm/pkcs7") -> Cryptor | None:
        if not work_key:
            return None
        ct = Cryptor(work_key, xform=xform)
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
