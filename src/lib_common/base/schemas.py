from typing import Generic

from pydantic import BaseModel, Field, ConfigDict

from .types import T, HostType, PortType, ExistPathType
from ..data.generator import UuidGenerator


# IP地址模型
class AddressM(BaseModel):
    host: HostType = "127.0.0.1"
    port: PortType = 8000


# 账号模型
class AccountM(BaseModel):
    username: str | None = None
    password: str | None = None


# 主机模型
class HostM(AddressM, AccountM): ...


# 基础设施
class InfraM(HostM):
    name: str = ""  # 名称
    category: str = ""  # 分类
    version: str = ""  # 版本
    description: str = ""  # 描述

    model_config = ConfigDict(extra="allow")

    @property
    def netloc(self) -> str:
        return f"{self.host}:{self.port}"

    @property
    def uuid(self) -> str:
        key = f"{self.category}:{self.cls}://{self.netloc}@{self.username}"
        return f"{UuidGenerator.by_value(key)}"



