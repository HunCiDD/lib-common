# 数据采集

from ..designs.factory import RegisterFactory
from .interface import ICollector, ICleaner, IStorager


# 数据采集工厂
class CollectorFactory(RegisterFactory[ICollector]):
    _map = {}


# 数据清洗工厂
class CleanerFactory(RegisterFactory[ICleaner]):
    _map = {}


# 数据存储工厂
class StoragerFactory(RegisterFactory[IStorager]):
    _map = {}
