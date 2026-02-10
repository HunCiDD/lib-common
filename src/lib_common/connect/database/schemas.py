from functools import lru_cache

from pydantic import BaseModel, Field, ConfigDict

from ...types import PathType

from ..core.schemas import Infra


# ------------------- Database Configuration -------------------
class DatabaseConfigs(BaseModel):
    """数据库配置"""

    type: str = Field(default="AsyncSQLAlchemyDBConnectionPool", description="类型")
    infra: Infra = Field(default_factory=Infra, description="基础设施配置")
    # 数据库类型 (mysql/postgresql/sqlite/oracle等)
    dialect: str
    # 驱动 (pymysql/psycopg2/cx_oracle等)
    driver: str | None = ""
    database: str | None = ""
    file: PathType | None = None
    pool_size: int = 5
    echo: bool = True

    model_config = ConfigDict(extra="ignore")
