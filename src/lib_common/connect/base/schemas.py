from pydantic import ConfigDict

from libs.common.data.generator import UuidGenerator
from libs.common.schemas import HostM


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
