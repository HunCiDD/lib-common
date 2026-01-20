from typing import Generic

from pydantic import BaseModel, Field, ConfigDict, SecretStr

from .types import T, HostType, PortType, UsernameType, PasswordType
from ..data.generator import UuidGenerator


# IP地址模型
class AddressM(BaseModel):
    host: HostType = Field(default="127.0.0.1", description="地址")
    port: PortType = Field(default=22, description="端口")


# 账号模型
class AccountM(BaseModel):
    username: str | None = None
    password: SecretStr | None = None


class AccountSafeM(BaseModel):
    username: UsernameType | None = None
    password: PasswordType | None = None


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


