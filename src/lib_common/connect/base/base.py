from typing import Any

from ...common.types import TypeMixin
from .schemas import InfraM


# ------------------- 请求 ---------------------
class BaseRequest(TypeMixin):
    AUTH = False  # 是否需要认证

    def __init__(self, **kwargs):
        self.kwargs = kwargs


# ------------------- 响应 ---------------------
class BaseResponse(TypeMixin):
    def __init__(self, code: int = 200, msg: str = "", data: Any = None, **kwargs):
        self.code = code
        self.msg = msg
        self.data = data
        self.kwargs = kwargs


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
