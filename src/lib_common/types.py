from typing import TypeVar, Annotated
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, BeforeValidator, StringConstraints, AfterValidator

from .constants import RegexPatterns
from lib_common.data.generator import DateTimeGenerator
from lib_common.data.converter import StringConverter
from lib_common.data.validates import (
    validate_bool,
    validate_host,
    validate_port,
    validate_int,
    validate_password,
    validate_path,
)


# 泛型
T = TypeVar("T")
# 模型泛型
SchemaAddT = TypeVar("SchemaAddT", bound=BaseModel)
SchemaSetT = TypeVar("SchemaSetT", bound=BaseModel)
SchemaGeTT = TypeVar("SchemaGeTT", bound=BaseModel)
SchemaDataT = TypeVar("SchemaDataT", bound=BaseModel)

# 何时使用 BeforeValidator：1-预处理原始输入数据，2-解析复杂字符串格式，3-数据格式转换
# 何时使用 AfterValidator：1-后处理验证结果，2-数据规范化，3-计算派生字段

# Bool类型
BoolType = Annotated[str | bool | int, AfterValidator(validate_bool)]
# 整型类型
IntType = Annotated[str | int, AfterValidator(validate_int)]
# 大写类型
UpperType = Annotated[str, BeforeValidator(StringConverter.to_upper)]
# 小写类型
LowerType = Annotated[str, BeforeValidator(StringConverter.to_lower)]
# 主机类型
HostType = Annotated[str, AfterValidator(validate_host)]
# 端口类型, 1 <= port <= 65535
PortType = Annotated[str | int, AfterValidator(validate_port), Field(ge=0, le=65535)]
# 路径类型
PathType = Annotated[str | Path, AfterValidator(lambda x: validate_path(x))]
ExistPathType = Annotated[str | Path, AfterValidator(lambda x: validate_path(x, exist=True))]

UsernameType = Annotated[
    str, StringConstraints(min_length=3, max_length=64, pattern=RegexPatterns.Username, strict=True)
]

PasswordType = Annotated[
    str,
    StringConstraints(min_length=8, max_length=128, strict=True),
    AfterValidator(validate_password),
]

DateTimeType = Annotated[
    datetime,
    Field(
        default_factory=DateTimeGenerator.now,
        description="本地时间",
        examples=[f"{DateTimeGenerator.now().strftime('%Y-%m-%d %H:%M:%S')}"],
    ),
]
