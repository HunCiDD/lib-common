from ...mixins import TypeMixin
from .schemas import InfraM

# ------------------- 连接池 ---------------------
class BaseConnectionPool(TypeMixin):
    def __init__(self, infra: InfraM, settings: dict = None, **kwargs):
        """
        :param infra:  基础设施信息
        :param settings:  配置信息
        :param kwargs:
        """
        self.infra = infra
        self.settings = settings or {}
        self.is_auth = False  # 是否已认证
        self.auth_cache = {}  # 认证缓存
        self.kwargs = kwargs