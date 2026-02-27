from typing import Annotated, TypeVar

from sqlalchemy import String
from sqlalchemy.orm import mapped_column

from ...data.utils.generator import UuidGenerator
from .base import BaseModel


M = TypeVar("M", bound=BaseModel)


PKType = Annotated[
    str,
    mapped_column(
        String(length=64),
        primary_key=True,
        default=lambda: str(UuidGenerator.by_time()),
    ),
]

FKType = Annotated[
    str,
    mapped_column(
        String(length=64),
    ),
]
