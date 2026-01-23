from pydantic import ConfigDict

from ..base.schemas import HostM


# # ------------------- Redis Configuration -------------------
class RedisConfigsM(HostM):
    """Redis配置"""

    database: str = ""

    model_config = ConfigDict(extra="ignore")

    @property
    def dsn(self) -> str:
        return ""
