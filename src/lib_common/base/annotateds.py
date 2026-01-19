
from typing import Annotated
from datetime import datetime

from pydantic import BeforeValidator, Field, StringConstraints

from ..data.generator import DateTimeGenerator
from ..data.regex import RegexPatterns
from ..data.validates import (
    validate_bool,
    validate_host,
    validate_port,
    validate_int,
    validate_lower,
    validate_password,
    validate_path,
    validate_upper,
)
from .types import BoolType, IntType, PathType


# Bool类型
BoolAnnotated = Annotated[BoolType, BeforeValidator(validate_bool)]
# 整型类型
IntAnnotated = Annotated[IntType, BeforeValidator(validate_int)]
# 大写类型
UpperAnnotated = Annotated[str, BeforeValidator(validate_upper)]
# 小写类型
LowerAnnotated = Annotated[str, BeforeValidator(validate_lower)]
# 主机类型
HostAnnotated = Annotated[str, BeforeValidator(validate_host)]
# 端口类型, 1 <= port <= 65535
PortAnnotated = Annotated[str | int, BeforeValidator(validate_port), Field(ge=0, le=65535)]
# 路径类型
PathAnnotated = Annotated[PathType, BeforeValidator(lambda x: validate_path(x))]
ExistPathAnnotated = Annotated[PathType, BeforeValidator(lambda x: validate_path(x, exist=True))]

UsernameType = Annotated[
    str, StringConstraints(min_length=3, max_length=64, pattern=RegexPatterns.Username, strict=True)
]

PasswordType = Annotated[
    str,
    StringConstraints(min_length=8, max_length=128, strict=True),
    BeforeValidator(validate_password),
]

DateTimeType = Annotated[
    datetime,
    Field(
        default_factory=DateTimeGenerator.now,
        description="本地时间",
        examples=[f"{DateTimeGenerator.now().strftime('%Y-%m-%d %H:%M:%S')}"],
    ),
]
