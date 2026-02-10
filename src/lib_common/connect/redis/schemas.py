from pydantic import ConfigDict

from ..core.schemas import Host


# # ------------------- Redis Configuration -------------------
class RedisConfigsM(Host):
    """Redis配置"""

    database: str = ""

    model_config = ConfigDict(extra="ignore")

    @property
    def dsn(self) -> str:
        return ""
