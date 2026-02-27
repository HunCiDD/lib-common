from ..settings import get_settings

from .manager import CryptorManager

# 全局加密器
cryptors = CryptorManager(settings=get_settings())
