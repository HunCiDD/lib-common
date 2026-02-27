from ..settings import get_settings

from .manager import LoggerManager


# 全局日志器
loggers = LoggerManager(settings=get_settings())
