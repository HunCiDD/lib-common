import os
import re
from collections.abc import Callable

from pydantic import BaseModel, Field, ConfigDict, field_validator, SecretStr

from ..base.constant import LOG_LEVELS
from ..base.types import BoolType, PathType, UpperType, IntType
from ..base.schemas import HostM


class AppConfigsM(BaseModel):
    """应用配置"""
    environment: str = Field(default="production", description="运行环境")
    root: str = Field(
        default=os.path.dirname(os.path.dirname(__file__)),
        description="项目根目录"
    )
    debug: bool = Field(default=False, description="调试模式")
    name: str = Field(default="fastapi", description="项目名称")
    version: str = Field(default="0.0.1", description="应用版本")
    host: str = Field(default="127.0.0.1", description="应用主机地址")
    port: int = Field(default=8000, description="应用端口号")
    tz: str = Field(default="Asia/Shanghai", description="应用时区")

    secret_key: SecretStr

    model_config = ConfigDict(extra="ignore")


class LoggerConfigsM(BaseModel):
    """日志器配置"""
    level: UpperType | None = "INFO"
    format: str | Callable | None = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    filter: str | Callable | None = None
    colorize: BoolType | None = None
    serialize: BoolType | None = None
    backtrace: BoolType | None = None
    diagnose: BoolType | None = None
    enqueue: BoolType | None = None
    catch: BoolType | None = None
    encoding: str | None = None
    retention: str | None = None
    rotation: str | None = None
    compression: str | None = None
    sensitive_fields: str = (
        "(password|token|key|secret|token|session|cookie|csrf|jwt|access_token|refresh_token"
        "|id_token|client_secret|client_id|api_key|secret_key)"
    )
    sensitive_fields_replacement: str = "********"
    max_length: IntType = 2000
    max_length_replacement: str = "..."

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    @field_validator("level")
    @classmethod
    def validate_level(cls, level: str) -> str:
        _level = level.upper()
        if _level not in LOG_LEVELS:
            raise ValueError(f"Invalid log level: {level}, must be one of {LOG_LEVELS}")
        return _level

    @field_validator("sensitive_fields")
    @classmethod
    def validate_sensitive_fields(cls, sensitive_fields: str) -> str:
        if not re.match(r"^\((\w+\|)*\w+\)$", sensitive_fields):
            raise ValueError
        return sensitive_fields


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


class RedisConfigsM(HostM):
    """Redis配置"""
    database: str = ""

    model_config = ConfigDict(extra="ignore")

    @property
    def dsn(self) -> str:
        return ""


class CryptorConfigsM(BaseModel):
    ...
