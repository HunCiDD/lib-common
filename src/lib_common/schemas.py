from pydantic import BaseModel, ConfigDict, Field, SecretStr

from .types import HostType, PortType, UsernameType, PasswordType


# IP地址模型
class Address(BaseModel):
    host: HostType = Field(default="127.0.0.1", description="地址")
    port: PortType = Field(default=22, description="端口")


# 账号模型
class Account(BaseModel):
    username: str | None = None
    password: SecretStr | None = None


class AccountSafe(BaseModel):
    username: UsernameType | None = None
    password: PasswordType | None = None


# 主机模型
class Host(Address, Account): ...



