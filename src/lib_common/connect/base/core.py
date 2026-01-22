from typing import Any

from ...mixins import TypeMixin
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



