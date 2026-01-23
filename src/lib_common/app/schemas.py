import os
from typing import List, Generic

from pydantic import BaseModel, Field, ConfigDict, SecretStr

from ..types import T, SchemaGeTT


class AppConfigsM(BaseModel):
    """应用配置"""

    environment: str = Field(default="production", description="运行环境")
    root: str = Field(default=os.path.dirname(os.path.dirname(__file__)), description="项目根目录")
    debug: bool = Field(default=False, description="调试模式")
    name: str = Field(default="fastapi", description="项目名称")
    version: str = Field(default="0.0.1", description="应用版本")
    host: str = Field(default="127.0.0.1", description="应用主机地址")
    port: int = Field(default=8000, description="应用端口号")
    tz: str = Field(default="Asia/Shanghai", description="应用时区")

    secret: SecretStr

    model_config = ConfigDict(extra="ignore")


class PageData(BaseModel, Generic[SchemaGeTT]):
    items: List[SchemaGeTT]
    page: int  # 页码
    size: int  # 单页数量
    total: int  # 总数量
    pages: int  # 总页数


class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(default=200, ge=0)
    message: str = ""
    data: T | None = None
