from typing import TypeVar, Literal
from pathlib import Path

# 泛型
T = TypeVar("T")

# Bool类型
BoolType = bool | Literal['true', 'false', 'True', 'False', 'TRUE', 'FALSE', 1, 0]
# 整型类型
IntType = str | int
# 路径类型
PathType = str | Path


