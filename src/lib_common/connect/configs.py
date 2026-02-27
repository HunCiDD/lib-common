from ..settings import get_settings

from .database.manager import DBInfraManager


# 全局数据库连接
databases = DBInfraManager(settings=get_settings())
