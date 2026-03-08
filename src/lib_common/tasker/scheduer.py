from threading import Lock

from celery.beat import ScheduleEntry, Scheduler
from celery.schedules import crontab

from ..configs import loggers

from connect.settings import DB
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
