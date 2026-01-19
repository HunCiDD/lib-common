from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from .types import PKType


class PKMixin:
    id: Mapped[PKType]


class TimeAtMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, comment="更新时间")
