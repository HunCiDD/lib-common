from pydantic import ConfigDict, BaseModel

from ...types import PathType
from ..base.schemas import HostM


# ------------------- Database Configuration -------------------
class DatabaseConfigsM(HostM):
    """数据库配置"""
    # 数据库类型 (mysql/postgresql/sqlite/oracle等)
    dialect: str
    # 驱动 (pymysql/psycopg2/cx_oracle等)
    driver: str | None = ""
    database: str | None = ""
    file: PathType | None = None
    echo: bool = True

    model_config = ConfigDict(extra="ignore")

    @property
    def dsn(self) -> str:
        return ""

