from typing import Dict
from sys import stdout
from pathlib import Path
import loguru

from ..designs.singleton import SingletonMeta
from ..config.settings import get_settings, Settings
from .loggers import LoggerFactory

SETTINGS = get_settings()


class LoggersManager(metaclass=SingletonMeta):
    _loggers: Dict[str, "loguru.Logger"] = {}
    _sink_maps: Dict[str, int] = {}

    def __init__(self, settings: Settings, **kwargs):
        self._settings = settings
        self._kwargs = kwargs
        self._init_loggers()

    def _init_loggers(self) -> None:
        """初始化日志记录器"""
        # 移除所有现有的sink
        loguru.logger.remove()
        # 非生产环境，初始化控制台
        if self._settings.app.environment != "production":
            self._init_console_logger()

    def _init_console_logger(self):
        common_configs = self._settings.loggers.get("common", {})
        console_configs = self._settings.loggers.get("console", {})
        merged_configs = {**common_configs, **console_configs}
        # 添加console
        self._add_logger("console", merged_configs)

    def _add_logger(self, key: str, key_settings: dict | None = None) -> "loguru.Logger | None":
        """
        添加日志记录器
        :param key: 键名
        :param key_settings: 配置
        :return:
        """
        if key_settings is None:
            key_settings = {}

        common_configs = self._settings.get("common", {})
        merged_configs = {**common_configs, **key_settings}
        if not merged_configs:
            return None

        if "sink" not in merged_configs:
            if key == "console":
                merged_configs["sink"] = stdout
            else:
                merged_configs["sink"] = Path(self._settings.app.root) / f"logs/{key}.log"

        logger_type = merged_configs.get("type", "FileLogger")
        logger_instance = LoggerFactory.create(logger_type, key, merged_configs, **self._kwargs)
        if logger_instance:
            self._loggers[key] = logger_instance.logger
            self._sink_maps[key] = logger_instance.sink_id
            return logger_instance.logger
        else:
            return None

    def add_logger(self, key: str, key_settings: dict | None = None) -> "loguru.Logger | None":
        """
        添加日志记录器
        :param key: 键名
        :param key_settings: 配置
        :return:
        """
        self.del_logger(key)
        return self._add_logger(key, key_settings)

    def get_logger(self, key: str) -> "loguru.Logger | None":
        """
        获取指定建的日志记录器
        :param key: 日志记录器的键名
        :return: 请求的日志记录器对象，如果不存在则返回None
        """
        if key in self._loggers:
            return self._loggers[key]

        # 不在缓存中，检查配置中是否存在，存在创建并返回
        if key in self._settings:
            key_settings = self._settings[key]
            return self._add_logger(key, key_settings)
        return None

    def del_logger(self, key: str) -> None:
        """
        删除指定建的日志记录器
        :param key: 要删除的日志记录器的键名
        :return:
        """
        sink_id = self._sink_maps.pop(key, None)
        if sink_id is not None:
            try:
                loguru.logger.remove(sink_id)
            except ValueError:
                # 如果sink已被其他方式移除，忽略错误
                pass

        if key in self._loggers:
            del self._loggers[key]
