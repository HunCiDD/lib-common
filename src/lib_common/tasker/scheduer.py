from threading import Lock
from datetime import datetime, UTC

from celery.beat import ScheduleEntry, Scheduler
from celery.schedules import crontab

from ..logger.configs import loggers
from ..connect.configs import databases
from .models import TaskCronJob

run_logger = loggers.get_logger("run")
local_db = databases.get_database("local")


class DatabaseSchedulerEntry(ScheduleEntry):
    """代表一个来自数据库的调度项"""

    def __init__(self, job: TaskCronJob):
        self.job = job
        try:
            # 将 "0 2 * * *" 拆分为 minute, hour, day_of_month, month_of_year, day_of_week
            parts = self.job.expression.strip().split()
            if len(parts) != 5:
                raise ValueError("Cron expression must have 5 fields")
            minute, hour, day_of_month, month_of_year, day_of_week = parts
            schedule = crontab(
                minute=minute,
                hour=hour,
                day_of_month=day_of_month,
                month_of_year=month_of_year,
                day_of_week=day_of_week,
            )
        except Exception as e:
            run_logger.error(f"Invalid cron expression {job}: {e}")
            # 使用一个永远不会触发的 cron，避免崩溃
            schedule = crontab(minute="*")  # 或抛出异常
            job.enabled = False  # 禁用无效任务

        super().__init__(
            name=self.job.name,
            task=self.job.t_name,
            schedule=schedule,
            args=self.job.t_args,
            kwargs=self.job.t_kwargs,
            options={"queue": "default"},
        )

    def is_due(self):
        if not self.job.enabled:
            # 返回 (is_due, next_time_in_seconds)
            return False, None

        last_run_at = self.job.next_run_at or datetime.now(UTC)
        return self.schedule.is_due(last_run_at)

    def __next__(self):
        # 更新下次运行时间（由 Celery 的 is_due 计算）
        if self.job.one_off:
            self.job.enabled = False
        # 注意：next_run_time 应由 Beat 在调度时更新，这里可暂不处理
        return self


class DatabaseScheduler(Scheduler):
    Entry = DatabaseSchedulerEntry

    def __init__(self, *args, **kwargs):
        self._schedules = {}
        self._last_updated = None
        self._lock = Lock()
        super().__init__(*args, **kwargs)

    def setup_schedule(self): ...

    def get_schedule(self):
        self._refresh_schedule()
        return self._schedules

    def _refresh_schedule(self):
        """从数据库加载定时任务，更新调度表"""
        with local_db.connection() as conn:
            jobs = conn.query(TaskCronJob).filter(TaskCronJob.enabled).all()
            new_schedule = {}
            for job in jobs:
                entry = self.Entry(job)
                new_schedule[entry.name] = entry
            self._schedule = new_schedule
            self._last_updated = datetime.now()

    def tick(self):
        """被 beat 循环调用，返回下次唤醒的秒数"""
        with self._lock:
            # 定期刷新调度表（比如每5分钟重新读取一次数据库，以便捕获新增/修改的任务）
            if not self._last_updated or (datetime.now() - self._last_updated).total_seconds() > 300:
                self._refresh_schedule()
            return super().tick()
