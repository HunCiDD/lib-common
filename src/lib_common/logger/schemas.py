import re
from collections.abc import Callable
from io import TextIOWrapper

from pydantic import BaseModel, ConfigDict, field_validator

from ..constants import LOG_LEVELS
from ..types import BoolType, PathType, UpperType, IntType


class LoggerConfigsM(BaseModel):
    """日志器配置"""

    sink: TextIOWrapper | PathType | None = None
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
        "|id_token|client_secret|client_id|api_key|secret)"
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
