from ...mixins import TypeMixin

from .schemas import Infra


# ------------------- 连接池 ---------------------
class BaseConnectionPool(TypeMixin):
    def __init__(self, infra: Infra, **kwargs):
        """
        :param infra:  基础设施信息
        :param kwargs:
        """
        self.infra = infra
        self.is_auth = False  # 是否已认证
        self.auth_cache = {}  # 认证缓存
        self.kwargs = kwargs
