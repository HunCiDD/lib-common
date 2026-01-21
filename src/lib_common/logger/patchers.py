from typing import List, Callable

import loguru

from ..config.schemas import LoggerConfigsM


class BasePatcher:
    _patchers: List[Callable] = []

    def __init__(self, name: str, configs: LoggerConfigsM):
        self.name = name
        self.configs = configs

    def call(self, record: "loguru.Record") -> None:
        for patch_func in self._patchers:
            # 返回False，表示记录将丢弃，没有必要执行后续的
            rst = patch_func(record, self)
            if not rst:
                return rst
        return None
