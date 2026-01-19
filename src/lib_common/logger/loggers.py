from typing import List, Callable
from abc import ABC, abstractmethod
from sys import stdout
from contextvars import ContextVar

import loguru

from ..designs.factory import RegisterFactory
from .schemas import ConsoleLoguruSettingsM, FileLoguruSettingsM
from .filters import BaseFilter, filter_name, filter_max_length, filter_sensitive_fields
from .patchers import BasePatcher


class BaseLogger(ABC):
    def __init__(self, name: str, settings: dict, **kwargs):
        self.name = name
        self.settings = settings
        self.kwargs = kwargs
        self._sink_id: int = -1
        self._logger: "loguru.Logger | None" = None
        self._init_logger()

    @property
    def logger(self) -> "loguru.Logger":
        if self._logger is None:
            raise Exception("Logger not initialized")
        return self._logger

    @property
    def sink_id(self) -> int:
        return self._sink_id

    @abstractmethod
    def _init_logger(self) -> None: ...

    def remove(self) -> None:
        """Remove the sink from logger"""
        if self._sink_id != -1:
            loguru.logger.remove(self._sink_id)
            self._sink_id = -1


class LoggerFactory(RegisterFactory[BaseLogger]):
    _map = {}


@LoggerFactory.register("ConsoleLogger")
class ConsoleLogger(BaseLogger):
    def _init_logger(self) -> None:
        _settings_m = ConsoleLoguruSettingsM(**self.settings)
        # 一定要启用Filter，否则导致bind 不生效
        params = _settings_m.model_dump(
            include={"level", "format", "colorize", "serialize", "backtrace", "enqueue", "diagnose", "context"},
            exclude_none=True,
        )
        params["sink"] = stdout
        self._sink_id = loguru.logger.add(**params)  # 保存sink_id
        self._logger = loguru.logger.bind(name=self.name)  # 使用self.name而不是硬编码


class FileFilter(BaseFilter):
    _filters: List[Callable] = [
        filter_name,
        filter_max_length,
        filter_sensitive_fields,
    ]


class FilePatcher(BasePatcher): ...


@LoggerFactory.register("FileLogger")
class FileLogger(BaseLogger):
    def _init_logger(self) -> None:
        _settings_m = FileLoguruSettingsM(**self.settings)
        # 一定要启用Filter，否则导致bind 不生效
        _filter = FileFilter(self.name, _settings_m)
        _settings_m.filter = _filter.call
        if hasattr(self, "_formatter"):
            _settings_m.format = self._formatter
        if not _settings_m.sink:
            raise Exception(f"{self.name} sink is required")  # 使用自定义异常
        params = _settings_m.model_dump(
            exclude={
                "type",
                "sensitive_fields",
                "sensitive_fields_replacement",
                "max_length",
                "max_length_replacement",
            },
            exclude_none=True,
        )
        self._sink_id = loguru.logger.add(**params)
        self._logger = loguru.logger.bind(name=self.name)  # 使用self.name而不是硬编码
        _patcher = FilePatcher(self.name, _settings_m)
        self._logger.patch(_patcher.call)


class AppLogContextVar:
    request_id_var: ContextVar[str] = ContextVar("request_id_var", default="N/A")


@LoggerFactory.register("AppLogger")
class AppLogger(FileLogger):

    @staticmethod
    def _formatter(record) -> str:
        request_id = AppLogContextVar.request_id_var.get()
        # 组装日志消息
        _message = (
            "{time:YYYY-MM-DD HH:mm:ss:SSS} | {level: <8} | {process}:{thread} | {name}:{function}:{line} | "
            + f"R-{request_id} |"
            + " {message}\n"
        )
        return _message

