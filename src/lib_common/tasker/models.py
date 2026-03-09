from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, ForeignKey, Text

from ..connect.database.base import BaseModel
from ..connect.database.mixins import PKMixin, TimeAtMixin


# 定时任务表设置
class TaskCronJob(PKMixin, BaseModel, TimeAtMixin):
    __tablename__ = "tasker_cron_jobs"
    name = Column(String(255), nullable=False)
    expression = Column(String(100), nullable=False)  # 表达式 如 "0 8 * * *"
    t_name = Column(String(255), nullable=False)  # 映射任务命令
    t_args = Column(JSON, default=[])
    t_kwargs = Column(JSON, default={})  # 任务关键字参数
    enabled = Column(Boolean, default=True)
    one_off = Column(Boolean, default=False)
    next_run_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<TaskerCronJob(id={self.id}, name={self.name}, expression={self.expression}>"


class TaskExecution(PKMixin, BaseModel):
    __tablename__ = "tasker_executions"

    job_id = Column(String, ForeignKey("tasker_cron_jobs.id"), nullable=True)
    status = Column(String(20), default="PENDING")
    args = Column(JSON, nullable=True)
    kwargs = Column(JSON, nullable=True)
    start_at = Column(DateTime(), nullable=False)
    end_at = Column(DateTime(), nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
