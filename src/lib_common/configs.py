
from .settings import get_settings

from .logger.manager import LoggerManager
from .cryptor.manager import CryptorManager


settings = get_settings()

loggers = LoggerManager(settings=settings)
cryptors = CryptorManager(settings=settings)
