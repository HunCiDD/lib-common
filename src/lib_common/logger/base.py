from typing import List, Callable
from abc import ABC, abstractmethod
from sys import stdout
from contextvars import ContextVar
import logging

import loguru

from ..designs.factory import RegisterFactory
from .schemas import LoggerConfigsM
from .filters import BaseFilter, filter_name, filter_max_length, filter_sensitive_fields
from .patchers import BasePatcher


# ==================== ✅ 拦截标准库日志 ====================
# class InterceptHandler(logging.Handler):
#         def emit(self, record):
#             # 获取 Loguru 对应的 level
#             try:
#                 level = logger.level(record.levelname).name
#             except ValueError:
#                 level = record.levelno
#             # 调用 Loguru，depth 调整调用栈深度，显示真实调用位置
#             logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())
#
#     # 替换 logging 根处理器
#     logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)
#
#     # 可选：按模块调整级别（清单 ✅ 按需级别）
#     # 例如将 uvicorn 访问日志提至 WARNING，减少干扰
#     logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
#     logging.getLogger("uvicorn.error").propagate = False  # 已由 Loguru 接管
#
#     logger.info(f"Loguru configured, env={env}, sample_rate={sample_rate}")


class BaseLogger(ABC):
    def __init__(self, name: str, configs: dict, **kwargs):
        self.name = name
        self.configs = configs
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
        _configs = LoggerConfigsM(**self.configs)
        # 一定要启用Filter，否则导致bind 不生效
        params = _configs.model_dump(
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
        _configs = LoggerConfigsM(**self.configs)
        # 一定要启用Filter，否则导致bind 不生效
        _filter = FileFilter(self.name, _configs)
        _configs.filter = _filter.call
        if hasattr(self, "_formatter"):
            _configs.format = self._formatter
        if not _configs.sink:
            raise Exception(f"{self.name} sink is required")  # 使用自定义异常
        params = _configs.model_dump(
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
        _patcher = FilePatcher(self.name, _configs)
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
