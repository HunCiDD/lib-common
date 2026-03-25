from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, Column, DateTime, String, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column

from ..connect.database.base import BaseModel
from ..connect.database.mixins import PKMixin, TimeAtMixin


class JobStatus(PyEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class JobConfig(PKMixin, BaseModel, TimeAtMixin):
    __tablename__ = "job_configs"

    # 任务名称
    name = Column(String(255), nullable=False, unique=True, comment="任务名称")
    # 任务描述
    description = Column(String(1023), nullable=True, comment="任务描述")
    #
    category = Column(String(32), nullable=False, default="date", comment="任务类型")
    expression = Column(String(125), nullable=True, comment="表达式 如 '0 8 * * *'")
    t_name = Column(String(255), nullable=False, comment="映射任务名称，a.b.c")
    t_args = Column(JSON, default=[])
    t_kwargs = Column(JSON, default={})
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")

    def __repr__(self) -> str:
        return f"<TaskConfigs(id={self.id}, name={self.name}, category={self.category}, expression={self.expression}>"


class JobRecord(PKMixin, BaseModel):
    __tablename__ = "job_records"

    config_id = Column(String, ForeignKey("job_configs.id"), nullable=True, comment="配置ID")
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False), nullable=False, default=JobStatus.pending, comment="任务状态"
    )
    args = Column(JSON, default=[], comment="任务运行参数")
    kwargs = Column(JSON, default={}, comment="任务运行关键参数")
    start_at = Column(DateTime(), nullable=True, comment="开始时间")
    end_at = Column(DateTime(), nullable=True, comment="结束时间")
    result = Column(JSON, nullable=True, comment="结果")
    error = Column(Text, nullable=True, comment="错误信息")
