from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, Integer, String

from ..connect.database.base import BaseModel
from ..connect.database.mixins import PKMixin


# 定时任务表设置
class TaskCrontab(PKMixin, BaseModel):
    __tablename__ = "task_crontabs"

    task_type = Column(String(64), nullable=False)
    task_params = Column(JSON(), nullable=False, default={})
    # Crontab 参数, *-每小说或每分 0-0点
    crontab = Column(String(64), nullable=False)
    # 是否启用
    is_active = Column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<TaskCrontab(id={self.id}, task_type={self.task_type}>"


class TaskRun(PKMixin, BaseModel):
    __tablename__ = "task_runs"

    # 来源
    source = Column(String(64), nullable=False)
    params = Column(JSON(), nullable=False, default={})
    status = Column(Enum("pending", "running", "success", "failed"), nullable=False, default="pending")
    start_datetime = Column(DateTime(), nullable=False)
    end_datetime = Column(DateTime(), nullable=True)
    duration = Column(Integer(), nullable=True)
    result = Column(JSON(), nullable=True)
    msg = Column(String(512), nullable=True)
