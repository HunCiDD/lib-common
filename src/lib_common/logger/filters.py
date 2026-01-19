from typing import List, Callable
import re

import loguru

from .schemas import LoguruSettingsM


# 基础过滤器
class BaseFilter:
    _filters: List[Callable] = []

    def __init__(self, name: str, settings: LoguruSettingsM):
        self.name = name
        self.settings = settings

    def call(self, record: "loguru.Record") -> bool:
        for filter_func in self._filters:
            # 返回False，表示记录将丢弃，没有必要执行后续的
            rst = filter_func(record, self)
            if not rst:
                return rst
        return True


def filter_name(record: "loguru.Record", filter_: BaseFilter, *args, **kwargs) -> bool:
    """
    # 过滤日志，只输出与自己相关的日志，eg：run.log 只接受 bind(name=run) 输出的日志
    """
    if record["extra"].get("name") != filter_.name:
        return False
    return True


def filter_sensitive_fields(record: "loguru.Record", filter_: BaseFilter, *args, **kwargs) -> bool:
    """安全日志过滤，敏感字段替换"""
    message = record.get("message")
    if not message:
        return True
    sensitive_fields = filter_.settings.sensitive_fields
    sensitive_fields_replacement = filter_.settings.sensitive_fields_replacement
    pattern = re.compile(rf"{sensitive_fields}([:=\s]+)(\w+)", re.IGNORECASE)
    new_message = re.sub(pattern, rf"\1\2{sensitive_fields_replacement}", message)
    record["message"] = new_message
    return True


def filter_max_length(record: "loguru.Record", filter_: BaseFilter, *args, **kwargs) -> bool:
    """
    过滤最大长度
    :param record:
    :param filter_:
    :param args:
    :param kwargs:
    :return:
    """
    message = record.get("message")
    if not message:
        return True

    max_length = filter_.settings.max_length
    max_length_replacement = filter_.settings.max_length_replacement
    if len(message) > max_length:
        record["message"] = f"{message[:max_length]}{max_length_replacement}"
    return True
