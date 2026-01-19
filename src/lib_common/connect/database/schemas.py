from pydantic import ConfigDict, BaseModel

from libs.common.types import PathType


# ------------------- Database Configuration -------------------
class DBSettingsM(BaseModel):
    # 数据库类型 (mysql/postgresql/sqlite/oracle等)
    dialect: str
    # 驱动 (pymysql/psycopg2/cx_oracle等)
    driver: str = ""
    database: str = ""
    pool_size: int = 5
    file: PathType | None = None
    echo: bool = True

    model_config = ConfigDict(extra="allow")


class SQLAlchemyDBSettingsM(DBSettingsM): ...
