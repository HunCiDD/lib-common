from .settings import get_settings

from .logger.manager import LoggerManager
from .cryptor.manager import CryptorManager
from .connect.database.manager import DBConnectionPoolManager


settings = get_settings()

# 全局日志器
loggers = LoggerManager(settings=settings)
# 全局加密器
cryptors = CryptorManager(settings=settings)
# 全局数据库连接
databases = DBConnectionPoolManager(settings=settings)
