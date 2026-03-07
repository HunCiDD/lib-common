from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, Integer, String

from ..connect.database.base import BaseModel
from ..connect.database.mixins import PKMixin


# 定时任务表设置
class TaskCrontab(PKMixin, BaseModel):
    __tablename__ = "task_crontabs"

    task_type = Column(String(64), nullable=False)
    task_params = Column(JSON(), nullable=False, default={})
    # Crontab 参数, *-每小说或每分 0-0点
    hour = Column(String(length=32), default="*")
    minute = Column(String(length=32), default="*")
    # 指定任务在每周的那几天
    day_of_week = Column(String(length=32), default="*")
    # 指定任务在每月的哪几天
    day_of_month = Column(String(length=32), default="*")
    # 指定任务在每年的哪几个月， 默认值*每月， 1,4 1月或4月  1-4 1到4月
    month_of_year = Column(String(length=32), default="*")

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


from threading import Lock

from celery import Celery
from celery.beat import ScheduleEntry, Scheduler
from celery.schedules import crontab

from ..configs import loggers, databases

from common.settings import SETTINGS, LOGGERS
from connect.settings import DB
from .settings import CELERY_SETTINGS
from .models import TaskCrontab

run_logger = loggers.get_logger("run")


class DefaultScheduler(Scheduler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = Lock()

    def _update_beat(self):
        run_logger.info("Update beat.")
        with DB.session() as session:
            db_task_crontabs = session.query(TaskCrontab).filter(TaskCrontab.is_active).all()

        schedule = {}
        for task_crontab in db_task_crontabs:
            if not isinstance(task_crontab, TaskCrontab):
                continue

            run_logger.debug(f"update celery beat [{task_crontab.id}]")

            ct = crontab(
                hour=str(task_crontab.hour),
                minute=str(task_crontab.minute),
                day_of_week=str(task_crontab.day_of_week),
                day_of_month=str(task_crontab.day_of_month),
                month_of_year=str(task_crontab.month_of_year),
            )

            entry = ScheduleEntry(
                name=str(task_crontab.id),
                task="src.appc_tasks.tasks.run_task",
                schedule=ct,
                args=(task_crontab.id, task_crontab.task_type, task_crontab.task_params),
            )
            schedule[task_crontab.id] = entry

        self.schedule = schedule

    def _update(self):
        try:
            with self._lock:
                self._update_beat()
        except Exception as e:
            run_logger.error(f"Failed to update schedule: {e}")

    def tick(self):  # type: ignore
        self._update()
        return super().tick()


from typing import Optional

from pydantic import BaseModel

from ..types import PathType, UpperType, LowerType


class WorkerConfigsM(BaseModel):
    logfile: Optional[PathType] = None
    loglevel: UpperType = "DEBUG"
    pool: LowerType = "threads"
    concurrency: int = 4


class BeatConfigsM(BaseModel):
    logfile: Optional[PathType] = None
    loglevel: UpperType = "DEBUG"


class CeleryConfigsM(BaseModel):
    broker: str
    backend: str
    worker: Optional[WorkerConfigsM] = None
    beat: Optional[BeatConfigsM] = None
