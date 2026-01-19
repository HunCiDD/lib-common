from typing import List, Callable

import loguru

from .schemas import LoguruSettingsM


class BasePatcher:
    _patchers: List[Callable] = []

    def __init__(self, name: str, settings: LoguruSettingsM):
        self.name = name
        self.settings = settings

    def call(self, record: "loguru.Record") -> None:
        for patch_func in self._patchers:
            # 返回False，表示记录将丢弃，没有必要执行后续的
            rst = patch_func(record, self)
            if not rst:
                return rst
