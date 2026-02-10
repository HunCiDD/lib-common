from typing import Annotated

from sqlalchemy import String
from sqlalchemy.orm import mapped_column

from lib_common.data.utils.generator import UuidGenerator


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
